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

    def test_create_chunks_example(self):
        self.assertEqual(chunking.create_chunks("2401.00001", "w1 w2 w3 w4 w5 w6 w7", 4, 1),
                         [chunking.Chunk("2401.00001", 0, "w1 w2 w3 w4"),
                          chunking.Chunk("2401.00001", 1, "w4 w5 w6 w7")])

    def test_create_chunks_positions_start_at_zero(self):
        positions = [chunk.position for chunk in chunking.create_chunks("doc", ZEHN_WOERTER, 4, 1)]
        self.assertEqual(positions, [0, 1, 2])

    def test_create_chunks_empty_text(self):
        self.assertEqual(chunking.create_chunks("doc", "", 4, 1), [])

    def test_create_chunks_empty_document_id(self):
        with self.assertRaises(ValueError):
            chunking.create_chunks("", ZEHN_WOERTER, 4, 1)

    def test_create_chunks_whitespace_document_id(self):
        with self.assertRaises(ValueError):
            chunking.create_chunks("   ", ZEHN_WOERTER, 4, 1)

    def test_create_chunks_invalid_parameters(self):
        with self.assertRaises(ValueError):
            chunking.create_chunks("doc", ZEHN_WOERTER, 4, 4)

    def test_chunk_is_immutable(self):
        chunk = chunking.Chunk("doc", 0, "text")
        with self.assertRaises(AttributeError):
            chunk.text = "anders"
