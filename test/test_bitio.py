import unittest
import itertools
from bonsai.bits import BitsIO


class BitstringIOTests(unittest.TestCase):
    def test_ue(self):
        for value, order in itertools.product((0, 123, 456), (0, 4, 10)):
            with self.subTest(value=value, order=order):
                bio = BitsIO()
                bio.write_ue(value, order)
                bio.seek(0)
                self.assertEqual(bio.read_ue(order), value)

    def test_se(self):
        bio = BitsIO()
        bio.write_se(-123456)
        bio.seek(0)
        self.assertEqual(bio.read_se(), -123456)


if __name__ == '__main__':
    unittest.main()