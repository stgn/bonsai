import unittest
import string
from collections import Counter
from bonsai.huffman import CanonicalCode
from bonsai.bits import BitsIO


def roundtrip(message, alphabet):
    counts = Counter(message)

    encoder = CanonicalCode.from_counts(counts)
    bw = BitsIO()
    encoder.write_codebook(alphabet, bw)
    bw.write_uint(len(message), 10)
    for c in message:
        encoder.write_symbol(c, bw)

    bw.seek(0)
    decoder = CanonicalCode.read_from_codebook(bw, alphabet)
    to_read = bw.read_uint(10)
    return ''.join(decoder.read_symbol(bw) for _ in range(to_read))


class HuffmanTests(unittest.TestCase):
    def test_basic(self):
        message = ('Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam quis dignissim turpis. '
                   'Praesent quis lobortis tortor, pretium tincidunt tortor. Sed bibendum lacus vitae orci egestas, '
                   'sit amet consequat leo auctor. Etiam sed turpis vitae neque turpis duis.')
        decoded = roundtrip(message, string.printable)
        self.assertEqual(message, decoded)

    def test_dense(self):
        # message includes all symbols in alphabet
        message = 'thequickbrownfoxjumpsoverthelazydog'
        alphabet = string.ascii_lowercase
        self.assertEqual(set(message), set(alphabet))
        decoded = roundtrip(message, alphabet)
        self.assertEqual(message, decoded)

    def test_construction(self):
        # this generates codes 0, 10, 110, 111
        coder = CanonicalCode('abcd', (1, 1, 2))
        codes = coder._build_code_map()
        self.assertDictEqual(codes, dict(a=(1, 0), b=(2, 0b10), c=(3, 0b110), d=(3, 0b111)))

        with self.assertRaises(ValueError):
            # not enough symbols
            CanonicalCode('a', (1,))

        with self.assertRaises(ValueError):
            # symbol and code length count mismatch
            CanonicalCode('abc', (1, 1, 2))

        with self.assertRaises(ValueError):
            # invalid code length count input
            # since there is no 3-bit code available after 111
            CanonicalCode('abcde', (1, 1, 3))

        with self.assertRaises(ValueError):
            # incomplete Huffman code/tree
            CanonicalCode('ab', (1, 1))

        with self.assertRaises(ValueError):
            # symbols are not unique
            CanonicalCode('aa', (2,))


if __name__ == '__main__':
    unittest.main()
