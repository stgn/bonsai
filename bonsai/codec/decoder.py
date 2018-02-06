import bonsai.specs as spec_types
from blist import blist
from collections import defaultdict, deque
from decimal import Decimal, DecimalTuple
from bonsai.bits import BitsIO
from bonsai.huffman import CanonicalCode
from bonsai.util import *

vardecimal = CanonicalCode((None, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9), (0, 1, 2, 8))


class GraphDecoder:
    __slots__ = ('spec', 'nodes', 'reader', 'string_table', 'used_types',
                 'recent_nodes', 'contexts', 'ctx_stack', 'tree')

    def __init__(self, fp, spec, string_table, tree=True):
        self.spec = spec
        self.tree = tree
        self.reader = BitsIO(fp)
        self.string_table = deque(string_table)

        self.used_types = [spec_types.Null]
        self.nodes = []
        self.recent_nodes = defaultdict(blist)
        self.contexts = {}
        self.ctx_stack = deque()

    def _decode_Enum(self, meta):
        bits = (len(meta.variants) - 1).bit_length()
        value = self.reader.read_uint(bits)
        return meta.variants[value]

    def _decode_Boolean(self, _):
        return self.reader.read_bool()

    def _decode_String(self, _):
        return self.string_table.popleft()

    def _decode_Number(self, _):
        digits = []
        while True:
            sym = vardecimal.read_symbol(self.reader)
            if sym is None:
                break
            digits.append(sym)

        sign = self.reader.read_bool() if digits else 0
        exponent = self.reader.read_se()

        decimal = Decimal(DecimalTuple(sign, digits, exponent))
        return float(decimal) if exponent else int(decimal)

    def _decode_List(self, meta):
        items = []
        if self.ctx_stack[-1] is not None:
            if meta.nonempty:
                items.append(self._decode_field(meta.of_type))
            while self.reader.read_bool():
                items.append(self._decode_field(meta.of_type))
        return tuple(items)

    def _decode_NodeRef(self, _):
        ctx = self.ctx_stack[-1]
        valid_types = ctx.symbols if isinstance(ctx, CanonicalCode) else [ctx]
        recent_ctx = self.recent_nodes[ctx]

        if self.reader.read_bool():
            rank = self.reader.read_ue(2)
            node_index = recent_ctx.pop(rank)
        else:
            if len(valid_types) >= 2:
                actual_type = ctx.read_symbol(self.reader)
            else:
                actual_type, = valid_types

            if actual_type != spec_types.Null:
                self.nodes.append(self._decode_node_inner(actual_type))
                node_index = len(self.nodes) - 1
            else:
                node_index = None

        if isinstance(node_index, int):
            recent_ctx.insert(0, node_index)
            return self.nodes[node_index] if self.tree else node_index

    def _decode_field(self, node_type):
        decode_fn = getattr(self, f'_decode_{node_type.__class__.__name__}')
        return decode_fn(node_type)

    def _decode_node_inner(self, node_type):
        node = {'type': node_type.__name__}
        for field_key, field_type in fields(node_type):
            self.ctx_stack.append(self.contexts.get((node_type, field_key)))
            node[field_key] = self._decode_field(field_type)
            self.ctx_stack.pop()
        return node

    def _prepare_huffman(self):
        for key, child_types in iter_fields(self.used_types, spec_types.NodeRef):
            if len(child_types) >= 2:
                if self.reader.read_bool():
                    ctx = CanonicalCode.read_from_codebook(self.reader, child_types)
                    self.contexts[key] = ctx
                else:
                    bits = (len(child_types) - 1).bit_length()
                    index = self.reader.read_uint(bits)
                    self.contexts[key] = child_types[index]
            elif child_types:
                self.contexts[key], = child_types

    def decode(self):
        all_types = subclasses(spec_types.Node)
        self.used_types.extend(x for x in all_types if self.reader.read_bool())

        self._prepare_huffman()
        decoded = self._decode_node_inner(self.spec.root_type)

        if self.tree:
            return decoded
        else:
            self.nodes.append(decoded)
            return self.nodes
