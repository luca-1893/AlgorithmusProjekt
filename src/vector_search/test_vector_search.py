import unittest

import vector_search


class TestCosineSimilarity(unittest.TestCase):
    def test_cosine_identical(self):
        self.assertAlmostEqual(vector_search.cosine_similarity([1, 2, 3], [1, 2, 3]), 1.0)

    def test_cosine_same_direction_different_length(self):
        self.assertAlmostEqual(vector_search.cosine_similarity([1, 2], [2, 4]), 1.0)

    def test_cosine_orthogonal(self):
        self.assertAlmostEqual(vector_search.cosine_similarity([1, 0], [0, 1]), 0.0)

    def test_cosine_opposite(self):
        self.assertAlmostEqual(vector_search.cosine_similarity([1, 1], [-1, -1]), -1.0)

    def test_cosine_hand_calculated(self):
        self.assertAlmostEqual(vector_search.cosine_similarity([1, 2, 2], [2, 0, 1]), 4 / (3 * 5 ** 0.5))

    def test_cosine_zero_vector(self):
        self.assertEqual(vector_search.cosine_similarity([0, 0], [1, 2]), 0.0)

    def test_cosine_different_lengths(self):
        with self.assertRaises(ValueError):
            vector_search.cosine_similarity([1, 2], [1, 2, 3])

    def test_cosine_empty_vectors(self):
        with self.assertRaises(ValueError):
            vector_search.cosine_similarity([], [])
