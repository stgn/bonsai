import logging
import bonsai.specs as spec_types
from blist import blist
from collections import deque, defaultdict, Counter
from decimal import Decimal
from bonsai.huffman import CanonicalCode
from bonsai.bits import BitsIO
from bonsai.util import *

logger = logging.getLogger(__name__)
vardecimal = CanonicalCode((None, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9), (0, 1, 2, 8))


class GraphEncoder:
    __slots__ = ('spec', 'nodes', 'tree', 'writer', 'string_table', 'used_types',
                 'recent_nodes', 'contexts', 'ctx_stack', 'index_cache')

    def __init__(self, spec, tree, fp):
        self.spec = spec
        self.tree = tree
        self.writer = BitsIO(fp)

        self.nodes = []
        self.string_table = []
        self.used_types = [spec_types.Null]
        self.recent_nodes = blist()
        self.contexts = {}
        self.ctx_stack = deque()
        self.index_cache = set()

    def _encode_Enum(self, meta, value):
        index = meta.variants.index(value)
        bits = (len(meta.variants) - 1).bit_length()
        self.writer.write_uint(index, bits)

    def _encode_Boolean(self, _, value):
        self.writer.write_bool(value)

    def _encode_String(self, _, value):
        self.string_table.append(value)

    def _encode_Number(self, _, value):
        dt = Decimal(value).as_tuple()

        digits = dt.digits if dt.digits != (0,) else ()
        for d in digits:
            vardecimal.write_symbol(d, self.writer)
        vardecimal.write_symbol(None, self.writer)

        if digits:
            self.writer.write_bool(dt.sign)

        self.writer.write_se(dt.exponent)

    def _encode_List(self, meta, items):
        if self.ctx_stack[-1] is not None:
            for i, item in enumerate(items):
                if not meta.nonempty or i > 0:
                    self.writer.write_bool(True)
                self._encode_field(meta.of_type, item)
            self.writer.write_bool(False)

    def _encode_NodeRef(self, _, node_index):
        ctx = self.ctx_stack[-1]
        valid_types = ctx.symbols if isinstance(ctx, CanonicalCode) else [ctx]

        if node_index in self.index_cache:
            # TODO: optimize this, or figure out a better way to accomplish the same idea
            # this takes up a MASSIVE amount (75%+) of the already slow encoding and decoding time
            # space savings aren't that great (smaller string table, but larger graph bitstream)

            rank = self.recent_nodes.index(node_index)

            # filter out nodes that would be invalid
            valid_recent_nodes = (x for x in self.recent_nodes
                                  if getattr(self.spec, self.nodes[x]['type']) in valid_types)
            valid_rank = next(i for i, x in enumerate(valid_recent_nodes) if x == node_index)

            # code rank using exp-Golomb
            self.writer.write_bool(True)
            self.writer.write_ue(valid_rank, 4)

            # we'll move the index to the front of the list
            del self.recent_nodes[rank]
        else:
            self.writer.write_bool(False)

            if isinstance(node_index, int):
                actual_node = self.nodes[node_index]
                actual_type = getattr(self.spec, actual_node['type'])
            else:
                actual_node = {}
                actual_type = spec_types.Null

            if len(valid_types) >= 2:
                ctx.write_symbol(actual_type, self.writer)

            self._encode_node_inner(actual_type, actual_node)

        if isinstance(node_index, int):
            self.index_cache.add(node_index)
            self.recent_nodes.insert(0, node_index)

    def _encode_field(self, node_type, value):
        encode_fn = getattr(self, f'_encode_{node_type.__class__.__name__}')
        encode_fn(node_type, value)

    def _encode_node_inner(self, node_type, node):
        for field_key, field_type in fields(node_type):
            self.ctx_stack.append(self.contexts.get((node_type, field_key)))
            self._encode_field(field_type, node[field_key])
            self.ctx_stack.pop()

    def _prepare_huffman(self, stats):
        for key, child_types in iter_fields(self.used_types, spec_types.NodeRef):
            if len(child_types) >= 2:
                type_counts = stats[key]

                if len(type_counts) >= 2:
                    self.writer.write_bool(True)
                    ctx = CanonicalCode.from_counts(type_counts)
                    ctx.write_codebook(child_types, self.writer)
                else:
                    self.writer.write_bool(False)
                    ctx, _ = type_counts.popitem()
                    bits = (len(child_types) - 1).bit_length()
                    index = child_types.index(ctx)
                    self.writer.write_uint(index, bits)

                self.contexts[key] = ctx
            elif child_types:
                # field can only have one type of node anyway
                self.contexts[key], = child_types

    def _graphify(self, tree):
        indices = {}
        type_stats = defaultdict(Counter)
        ctx_stack = deque([None])

        def traverse(node):
            ctx_type, ctx_field = ctx_stack[-1] or (None, None)
            if isinstance(node, dict):
                if 'type' in node:
                    real_type = getattr(self.spec, node['type'])
                    type_stats[ctx_type, ctx_field][real_type] += 1

                    for k, v in node.items():
                        ctx_stack.append((real_type, k))
                        node[k] = traverse(v)
                        ctx_stack.pop()

                    flat_node = tuple(node.items())
                    try:
                        index = indices[flat_node]
                    except KeyError:
                        index = len(self.nodes)
                        self.nodes.append(node)
                        indices[flat_node] = index

                    return index
                else:
                    return tuple(node.items())
            elif isinstance(node, list):
                return tuple(map(traverse, node))
            elif node is None:
                type_stats[ctx_type, ctx_field][spec_types.Null] += 1
            return node

        traverse(tree)
        return type_stats

    def encode(self):
        type_stats = self._graphify(self.tree)

        # TODO: filter out Node types that shouldn't be codeable
        all_types = subclasses(spec_types.Node)
        used_types_set = {getattr(self.spec, x['type']) for x in self.nodes}
        for x in all_types:
            self.writer.write_bool(x in used_types_set)
        self.used_types.extend(x for x in all_types if x in used_types_set)

        self._prepare_huffman(type_stats)
        logger.debug(f'Codebook size: {self.writer.tell()} bits')

        self._encode_node_inner(self.spec.root_type, self.nodes[-1])

        self.writer.flush()

        return self.string_table
