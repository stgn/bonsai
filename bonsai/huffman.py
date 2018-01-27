import queue
import collections


class HuffmanNode:
    __slots__ = ('weight',)

    def __init__(self, weight):
        self.weight = weight

    def __lt__(self, other):
        return self.weight < other.weight


class LeafNode(HuffmanNode):
    __slots__ = ('symbol',)

    def __init__(self, weight, symbol):
        super().__init__(weight)
        self.symbol = symbol


class InternalNode(HuffmanNode):
    __slots__ = ('left', 'right')

    def __init__(self, weight, left, right):
        super().__init__(weight)
        self.left = left
        self.right = right


def construct_tree(counts):
    """
    Constructs a Huffman tree from a mapping of symbols to frequency counts.
    :rtype: InternalNode or LeafNode
    """
    pq = queue.PriorityQueue()

    for s, c in counts.items():
        pq.put(LeafNode(c, s))

    while pq.qsize() > 1:
        a, b = pq.get(), pq.get()
        n = InternalNode(a.weight + b.weight, a, b)
        pq.put(n)

    return pq.get()


def code_lengths(tree):
    """
    Returns a mapping of symbols to code lengths from a Huffman tree.
    :type tree: InternalNode or LeafNode
    :rtype: dict
    """
    lengths = {}

    def traverse(node, depth):
        if isinstance(node, LeafNode):
            lengths[node.symbol] = depth
        elif isinstance(node, InternalNode):
            traverse(node.left, depth + 1)
            traverse(node.right, depth + 1)
        else:
            raise ValueError('Unexpected node type')

    traverse(tree, 0)
    return lengths


class DecodeError(Exception):
    """Represents an error while attempting to read a symbol."""
    pass


class CanonicalCode:
    """A canonical Huffman encoder/decoder."""

    __slots__ = ('symbols', 'length_counts', 'code_map')

    def __init__(self, symbols, length_counts):
        """
        Constructs a canonical Huffman encoder/decoder.
        :param symbols: A sequence of symbols.
        :param length_counts: A sequence of code bit length counts.
        """
        if len(symbols) < 2:
            raise ValueError('Two or more symbols required')

        if len(symbols) != sum(length_counts):
            raise ValueError('Symbol/code count mismatch')

        symbol_set = set()
        if any(i in symbol_set or symbol_set.add(i) for i in symbols):
            raise ValueError('Symbols are not unique')

        count = slots = 0
        length_slots = self._length_slots(length_counts)
        for count, slots in length_slots:
            if count > slots:
                raise ValueError('Not enough codes available for length')
        if count < slots:
            raise ValueError('Incomplete Huffman code')

        self.symbols = symbols
        self.length_counts = length_counts
        self.code_map = None

    def _build_code_map(self):
        """
        Prepares a mapping of symbols to codes for encoding.
        """
        code_map = {}
        code = index = 0
        for length, count in enumerate(self.length_counts, 1):
            code_map.update({self.symbols[index + x]: (length, code + x)
                             for x in range(count)})
            code = (code + count) << 1
            index += count
        return code_map

    @classmethod
    def from_code_lengths(cls, lengths):
        """
        Returns an instance from a mapping of symbols to code lengths.
        :param lengths: A mapping of symbols to code lengths.
        :rtype: CanonicalCode
        """
        counter = collections.Counter(lengths.values())
        symbols = sorted(lengths, key=lengths.get)
        length_counts = [counter[x + 1] for x in range(max(counter))]
        return cls(symbols, length_counts)

    @classmethod
    def from_counts(cls, counts):
        """
        Returns an instance from a mapping of symbols to frequency counts.
        :param counts: A mapping of symbols to frequency counts.
        :rtype: CanonicalCode
        """
        tree = construct_tree(counts)
        lengths = code_lengths(tree)
        return cls.from_code_lengths(lengths)

    def write_symbol(self, symbol, writer):
        """
        Writes a symbol to the bitstream.
        :param symbol: The symbol to write.
        :param writer: The stream to write the symbol to.
        """
        if not self.code_map:
            self.code_map = self._build_code_map()

        length, code = self.code_map[symbol]
        writer.write_uint(code, length)

    def read_symbol(self, reader):
        """
        Reads a symbol from the bitstream.
        :param reader: The stream to read the symbol from.
        :return: A symbol.
        """
        code = first = index = 0
        for count in self.length_counts:
            code = code << 1 | reader.read_uint(1)
            if code - count < first:
                return self.symbols[index + (code - first)]
            index += count
            first = (first + count) << 1

        raise DecodeError('Max code length exceeded while reading symbol')

    def write_codebook(self, alphabet, writer):
        """
        Serializes the codebook to the stream.
        :param alphabet: A known sequence containing the symbols in the codebook.
        :param writer: The stream to write the codebook to.
        """
        alphabet = list(alphabet)

        for count, slots in self._length_slots(self.length_counts):
            count_bits = slots.bit_length()
            writer.write_uint(count, count_bits)

        for symbol in self.symbols:
            len_bits = (len(alphabet) - 1).bit_length()
            index = alphabet.index(symbol)
            writer.write_uint(index, len_bits)
            alphabet.pop(index)

    @classmethod
    def read_from_codebook(cls, reader, alphabet):
        """
        Reads a canonical Huffman codebook from the stream.
        :param reader: The stream to read the codebook from.
        :param alphabet: A known sequence from which symbols will be taken.
        :rtype: CanonicalCode
        """
        alphabet = list(alphabet)
        length_counts = []
        symbols = []

        slots = 2
        while slots:
            count_bits = slots.bit_length()
            count = reader.read_uint(count_bits)
            length_counts.append(count)
            slots = (slots - count) << 1

        num_symbols = sum(length_counts)
        for x in range(num_symbols):
            len_bits = (len(alphabet) - 1).bit_length()
            index = reader.read_uint(len_bits)
            symbols.append(alphabet[index])
            alphabet.pop(index)

        return cls(symbols, length_counts)

    @staticmethod
    def _length_slots(length_counts):
        """
        Yields the number of codes available for each code length.
        """
        slots = 2
        for count in length_counts:
            yield count, slots
            slots = (slots - count) << 1
