import unittest

from tiny_variable_length_integer_varint import decode, encode


class EncodeTests(unittest.TestCase):
    def test_zero_is_one_byte(self):
        self.assertEqual(encode(0), b"\x00")

    def test_small_values_are_one_byte(self):
        for value in (1, 2, 42, 127):
            with self.subTest(value=value):
                self.assertEqual(encode(value), bytes([value]))

    def test_boundary_128_needs_two_bytes(self):
        self.assertEqual(encode(128), b"\x80\x01")

    def test_300_matches_known_encoding(self):
        # 300 = 0b100101100 -> low 7 bits 0101100, high bits 10.
        self.assertEqual(encode(300), b"\xac\x02")

    def test_max_uint64(self):
        self.assertEqual(
            encode(0xFFFFFFFFFFFFFFFF),
            b"\xff\xff\xff\xff\xff\xff\xff\xff\xff\x01",
        )

    def test_negative_rejected(self):
        with self.assertRaises(ValueError):
            encode(-1)

    def test_non_integer_rejected(self):
        with self.assertRaises(TypeError):
            encode(1.5)  # type: ignore[arg-type]


class DecodeTests(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(decode(b"\x00"), (0, 1))

    def test_single_byte(self):
        self.assertEqual(decode(b"\x7f"), (127, 1))

    def test_two_byte(self):
        self.assertEqual(decode(b"\x80\x01"), (128, 2))

    def test_300(self):
        self.assertEqual(decode(b"\xac\x02"), (300, 2))

    def test_max_uint64(self):
        data = b"\xff\xff\xff\xff\xff\xff\xff\xff\xff\x01"
        self.assertEqual(decode(data), (0xFFFFFFFFFFFFFFFF, 10))

    def test_offset_is_respected(self):
        data = b"\x00\xac\x02\xff"
        self.assertEqual(decode(data, offset=1), (300, 2))

    def test_round_trip_many_values(self):
        values = [0, 1, 127, 128, 255, 256, 16383, 16384, 1 << 32, (1 << 64) - 1]
        for value in values:
            with self.subTest(value=value):
                encoded = encode(value)
                decoded, length = decode(encoded)
                self.assertEqual(decoded, value)
                self.assertEqual(length, len(encoded))

    def test_truncated_buffer_raises_index_error(self):
        with self.assertRaises(IndexError):
            decode(b"\x80")

    def test_offset_past_end_raises_value_error(self):
        with self.assertRaises(ValueError):
            decode(b"\x00", offset=2)

    def test_negative_offset_raises_value_error(self):
        with self.assertRaises(ValueError):
            decode(b"\x00", offset=-1)

    def test_too_many_bytes_raises_value_error(self):
        # Eleven continuation bytes: the decoder should refuse rather than
        # silently build an unbounded integer.
        with self.assertRaises(ValueError):
            decode(b"\x80" * 10 + b"\x01")

    def test_bytearray_is_accepted(self):
        self.assertEqual(decode(bytearray(b"\xac\x02")), (300, 2))

    def test_memoryview_is_accepted(self):
        self.assertEqual(decode(memoryview(b"\xac\x02")), (300, 2))


if __name__ == "__main__":
    unittest.main()
