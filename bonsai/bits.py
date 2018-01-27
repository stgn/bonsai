import abc
import itertools
from io import BytesIO


class BitsIOBase(abc.ABC):
    __slots__ = ()

    @abc.abstractmethod
    def seek(self, pos):
        """Seeks to a position in the bitstream."""

    @abc.abstractmethod
    def tell(self):
        """Returns the current position in the bitstream."""

    @abc.abstractmethod
    def flush(self):
        """Flush buffers to the stream."""

    @abc.abstractmethod
    def write_uint(self, value, bits):
        """Writes an unsigned integer of a given number of bits to the bitstream."""

    @abc.abstractmethod
    def read_uint(self, bits):
        """Reads an unsigned integer of a given number of bits from the bitstream."""

    def write_bool(self, value):
        """Writes a boolean to the bitstream."""
        self.write_uint(int(value), 1)

    def read_bool(self):
        """Reads a boolean from the bitstream."""
        return bool(self.read_uint(1))

    def write_ue(self, value, order=0):
        """Writes an unsigned exponential-Golomb-coded integer of a given order to the bitstream."""
        if order:
            q = value >> order
            r = value & (1 << order) - 1
            self.write_ue(q, 0)
            self.write_uint(r, order)
        else:
            bits = (value + 1).bit_length() * 2 - 1
            self.write_uint(value + 1, bits)

    def read_ue(self, order=0):
        """Reads an unsigned exponential-Golomb-coded integer of a given order from the bitstream."""
        if order:
            q = self.read_ue(0)
            r = self.read_uint(order)
            return (q << order) | r
        else:
            for x in itertools.count():
                # read 1, 2, 4, 8... bits until we hit non-zero
                bits = 1 << x
                last = self.read_uint(bits)
                if last:
                    to_get = 2 * (bits - last.bit_length())
                    break
            return ((last << to_get) | self.read_uint(to_get)) - 1

    def write_se(self, value, order=0):
        """Writes a signed exponential-Golomb-coded integer of a given order to the bitstream."""
        value = 2 * value - 1 if value > 0 else -2 * value
        self.write_ue(value, order)

    def read_se(self, order=0):
        """Reads a signed exponential-Golomb-coded integer of a given order from the bitstream."""
        value = self.read_ue(order)
        q, r = value >> 1, value & 1
        return q + 1 if r else -q


class BitsIO(BitsIOBase):
    __slots__ = ('fp', 'bit_pos', 'bit_buf')

    def __init__(self, fp=None):
        if fp is None:
            fp = BytesIO()
        self.fp = fp
        self.bit_pos = 0
        self.bit_buf = None

    def seek(self, pos):
        self.flush()  # uh...
        byte, bit = pos >> 3, pos & 7
        self.fp.seek(byte)
        self.bit_pos = bit

    def tell(self):
        return (self.fp.tell() << 3) + self.bit_pos

    def flush(self):
        if self.bit_pos and self.fp.writable():
            self.fp.write(bytes((self.bit_buf,)))
        self.bit_buf = None
        self.bit_pos = 0

    def write_uint(self, value, bits):
        while bits:
            if self.bit_buf is None:
                self.bit_buf = 0

            to_put = min(8 - self.bit_pos, bits)
            in_shift = bits - to_put
            out_shift = 8 - to_put - self.bit_pos
            mask = (1 << to_put) - 1

            value_part = value >> in_shift & mask
            self.bit_buf |= value_part << out_shift

            bits -= to_put
            self.bit_pos += to_put
            if self.bit_pos >= 8:
                self.flush()

    def read_uint(self, bits):
        if self.bit_buf is None:
            self.bit_buf = ord(self.fp.read(1))

        result = 0

        while bits:
            to_get = min(8 - self.bit_pos, bits)
            shift = 8 - to_get - self.bit_pos
            mask = (1 << to_get) - 1

            result <<= to_get
            result |= self.bit_buf >> shift & mask

            bits -= to_get
            self.bit_pos += to_get
            if self.bit_pos >= 8:
                self.bit_buf = ord(self.fp.read(1))
                self.bit_pos = 0

        return result