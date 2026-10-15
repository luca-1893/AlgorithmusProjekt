import unittest

import vector_search


class TestCosineSimilarity(unittest.TestCase):
    def test_cosine_different_lengths(self):
        with self.assertRaises(ValueError):
            vector_search.cosine_similarity([1, 2], [1, 2, 3])

    def test_cosine_empty_vectors(self):
        with self.assertRaises(ValueError):
            vector_search.cosine_similarity([], [])

    def test_cosine_hand_calculated(self):
        self.assertAlmostEqual(vector_search.cosine_similarity([1, 2, 2], [2, 0, 1]), 4 / (3 * 5 ** 0.5))

    def test_cosine_identical(self):
        self.assertAlmostEqual(vector_search.cosine_similarity([1, 2, 3], [1, 2, 3]), 1.0)

    def test_cosine_in_range(self):
        for a, b in [([3, -1, 2], [-2, 5, 1]), ([0.1, 0.2], [100, -50]), ([1], [-7])]:
            self.assertTrue(-1.0 <= vector_search.cosine_similarity(a, b) <= 1.0)

    def test_cosine_opposite(self):
        self.assertAlmostEqual(vector_search.cosine_similarity([1, 1], [-1, -1]), -1.0)

    def test_cosine_orthogonal(self):
        self.assertAlmostEqual(vector_search.cosine_similarity([1, 0], [0, 1]), 0.0)

    def test_cosine_same_direction_different_length(self):
        self.assertAlmostEqual(vector_search.cosine_similarity([1, 2], [2, 4]), 1.0)

    def test_cosine_symmetric(self):
        self.assertAlmostEqual(vector_search.cosine_similarity([1, 2, 2], [2, 0, 1]),
                               vector_search.cosine_similarity([2, 0, 1], [1, 2, 2]))

    def test_cosine_zero_vector(self):
        self.assertEqual(vector_search.cosine_similarity([0, 0], [1, 2]), 0.0)


class TestTopK(unittest.TestCase):
    def test_top_k_does_not_change_input(self):
        scores = [0.2, 0.9, 0.5]
        vector_search.top_k(scores, 2)
        self.assertEqual(scores, [0.2, 0.9, 0.5])

    def test_top_k_empty_scores(self):
        self.assertEqual(vector_search.top_k([], 3), [])

    def test_top_k_example(self):
        self.assertEqual(vector_search.top_k([0.2, 0.9, 0.5, 0.7], 2), [(1, 0.9), (3, 0.7)])

    def test_top_k_larger_than_list(self):
        self.assertEqual(vector_search.top_k([0.3, 0.6], 5), [(1, 0.6), (0, 0.3)])

    def test_top_k_length_is_min_of_k_and_n(self):
        for k in range(1, 7):
            self.assertEqual(len(vector_search.top_k([0.3, 0.1, 0.9, 0.5], k)), min(k, 4))

    def test_top_k_matches_full_sort(self):
        scores = [0.42, 0.17, 0.93, 0.05, 0.61, 0.88, 0.29, 0.74]
        expected = sorted(enumerate(scores), key=lambda item: -item[1])[:3]
        self.assertEqual(vector_search.top_k(scores, 3), expected)

    def test_top_k_negative_scores(self):
        self.assertEqual(vector_search.top_k([-0.5, -0.1, -0.9], 1), [(1, -0.1)])

    def test_top_k_sorted_descending(self):
        scores = [score for _, score in vector_search.top_k([0.1, 0.4, 0.3, 0.8, 0.6], 5)]
        self.assertEqual(scores, [0.8, 0.6, 0.4, 0.3, 0.1])

    def test_top_k_ties_keep_lower_position(self):
        self.assertEqual(vector_search.top_k([0.5, 0.5, 0.5], 2), [(0, 0.5), (1, 0.5)])

    def test_top_k_zero(self):
        with self.assertRaises(ValueError):
            vector_search.top_k([0.1], 0)


class TestMostSimilar(unittest.TestCase):
    def test_most_similar_dimension_mismatch(self):
        with self.assertRaises(ValueError):
            vector_search.most_similar([1, 0], [[1, 0, 0]], 1)

    def test_most_similar_example(self):
        candidates = [[0, 1], [1, 0], [1, 1]]
        result = vector_search.most_similar([1, 0], candidates, 2)
        self.assertEqual([position for position, _ in result], [1, 2])

    def test_most_similar_no_candidates(self):
        self.assertEqual(vector_search.most_similar([1, 0], [], 3), [])

    def test_most_similar_scores(self):
        result = vector_search.most_similar([1, 0], [[1, 1]], 1)
        self.assertAlmostEqual(result[0][1], 1 / 2 ** 0.5)


class FakeEmbedder(vector_search.Embedder):
    def __init__(self, vectors):
        self.vectors = vectors
        self.calls = []

    def _request(self, texts):
        self.calls.append(texts)
        return self.vectors


class TestEmbedder(unittest.TestCase):
    def test_embed_empty_vector(self):
        with self.assertRaises(vector_search.EmbeddingError):
            FakeEmbedder([[]]).embed(["a"])

    def test_embed_empty_without_request(self):
        embedder = FakeEmbedder([])
        self.assertEqual(embedder.embed([]), [])
        self.assertEqual(embedder.calls, [])

    def test_embed_returns_vectors(self):
        embedder = FakeEmbedder([[1.0, 0.0], [0.0, 1.0]])
        self.assertEqual(embedder.embed(["a", "b"]), [[1.0, 0.0], [0.0, 1.0]])

    def test_embed_unequal_lengths(self):
        with self.assertRaises(vector_search.EmbeddingError):
            FakeEmbedder([[1.0, 0.0], [1.0]]).embed(["a", "b"])

    def test_embed_wrong_count(self):
        with self.assertRaises(vector_search.EmbeddingError):
            FakeEmbedder([[1.0, 0.0]]).embed(["a", "b"])

    def test_embedder_is_abstract(self):
        with self.assertRaises(TypeError):
            vector_search.Embedder()


DUPLICATE_VECTORS = [[1.0, 0.0], [1.0, 0.01], [0.0, 1.0]]


class TestMmrSelect(unittest.TestCase):
    def test_mmr_does_not_mutate_input(self):
        relevance = [1.0, 0.95, 0.6]
        vectors = [list(vector) for vector in DUPLICATE_VECTORS]
        vector_search.mmr_select(relevance, vectors, 2, 0.5)
        self.assertEqual((relevance, vectors), ([1.0, 0.95, 0.6], DUPLICATE_VECTORS))

    def test_mmr_first_pick_is_most_relevant(self):
        self.assertEqual(vector_search.mmr_select([0.2, 0.9, 0.5], DUPLICATE_VECTORS, 1, 0.5), [1])

    def test_mmr_k_larger_than_candidates(self):
        self.assertEqual(sorted(vector_search.mmr_select([1.0, 0.5, 0.2], DUPLICATE_VECTORS, 10)), [0, 1, 2])

    def test_mmr_k_zero(self):
        with self.assertRaises(ValueError):
            vector_search.mmr_select([1.0], [[1.0]], 0)

    def test_mmr_lambda_one_is_pure_relevance(self):
        self.assertEqual(vector_search.mmr_select([1.0, 0.95, 0.6], DUPLICATE_VECTORS, 2, 1.0), [0, 1])

    def test_mmr_lambda_out_of_range(self):
        with self.assertRaises(ValueError):
            vector_search.mmr_select([1.0], [[1.0]], 1, 1.5)

    def test_mmr_length_mismatch(self):
        with self.assertRaises(ValueError):
            vector_search.mmr_select([1.0], DUPLICATE_VECTORS, 1)

    def test_mmr_no_candidates(self):
        self.assertEqual(vector_search.mmr_select([], [], 3), [])

    def test_mmr_selects_each_position_once(self):
        selected = vector_search.mmr_select([0.9, 0.8, 0.7, 0.6], [[1, 0], [1, 0], [0, 1], [0, 1]], 4, 0.3)
        self.assertEqual(len(selected), len(set(selected)))

    def test_mmr_skips_near_duplicate(self):
        self.assertEqual(vector_search.mmr_select([1.0, 0.95, 0.6], DUPLICATE_VECTORS, 2, 0.5), [0, 2])

    def test_mmr_ties_keep_lower_position(self):
        self.assertEqual(vector_search.mmr_select([0.5, 0.5], [[1.0, 0.0], [0.0, 1.0]], 1), [0])
