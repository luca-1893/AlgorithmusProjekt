import unittest
import chunking

ZEHN_WOERTER = "w1 w2 w3 w4 w5 w6 w7 w8 w9 w10"


class TestChunking(unittest.TestCase):
    def test_split_example_with_overlap(self):
        self.assertEqual(chunking.split_into_chunks(ZEHN_WOERTER, 4, 1),
                         ["w1 w2 w3 w4", "w4 w5 w6 w7", "w7 w8 w9 w10"])

    def test_split_without_overlap(self):
        self.assertEqual(chunking.split_into_chunks(ZEHN_WOERTER, 5, 0),
                         ["w1 w2 w3 w4 w5", "w6 w7 w8 w9 w10"])

    def test_split_shorter_than_chunk(self):
        self.assertEqual(chunking.split_into_chunks("w1 w2 w3", 5, 1), ["w1 w2 w3"])

    def test_split_exactly_one_chunk(self):
        self.assertEqual(chunking.split_into_chunks("w1 w2 w3 w4", 4, 1), ["w1 w2 w3 w4"])

    def test_split_no_chunk_of_only_overlap(self):
        self.assertEqual(chunking.split_into_chunks("w1 w2 w3 w4 w5 w6 w7", 4, 1),
                         ["w1 w2 w3 w4", "w4 w5 w6 w7"])

    def test_split_short_last_chunk(self):
        self.assertEqual(chunking.split_into_chunks("w1 w2 w3 w4 w5 w6 w7 w8", 4, 1),
                         ["w1 w2 w3 w4", "w4 w5 w6 w7", "w7 w8"])

    def test_split_normalizes_whitespace(self):
        self.assertEqual(chunking.split_into_chunks("w1\n\nw2   w3\tw4", 10, 0), ["w1 w2 w3 w4"])

    def test_split_empty_string(self):
        self.assertEqual(chunking.split_into_chunks("", 4, 1), [])

    def test_split_only_whitespace(self):
        self.assertEqual(chunking.split_into_chunks("  \n ", 4, 1), [])

    def test_split_chunk_size_zero(self):
        with self.assertRaises(ValueError):
            chunking.split_into_chunks(ZEHN_WOERTER, 0, 0)

    def test_split_negative_overlap(self):
        with self.assertRaises(ValueError):
            chunking.split_into_chunks(ZEHN_WOERTER, 4, -1)

    def test_split_overlap_equals_chunk_size(self):
        with self.assertRaises(ValueError):
            chunking.split_into_chunks(ZEHN_WOERTER, 4, 4)

    def test_split_overlap_greater_than_chunk_size(self):
        with self.assertRaises(ValueError):
            chunking.split_into_chunks(ZEHN_WOERTER, 4, 5)
