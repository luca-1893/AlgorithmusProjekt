import unittest

import ranking


class TestReciprocalRankFusion(unittest.TestCase):
    def test_rrf_hand_calculated(self):
        result = ranking.reciprocal_rank_fusion([[1, 2], [2, 3]], k_rrf=0)
        self.assertEqual([candidate_id for candidate_id, _ in result], [2, 1, 3])
        self.assertAlmostEqual(dict(result)[2], 1 / 2 + 1 / 1)

    def test_rrf_default_constant(self):
        result = ranking.reciprocal_rank_fusion([[7]])
        self.assertAlmostEqual(result[0][1], 1 / 61)

    def test_rrf_candidate_in_both_lists_wins(self):
        result = ranking.reciprocal_rank_fusion([[1, 2, 3], [3, 4, 5]])
        self.assertEqual(result[0][0], 3)

    def test_rrf_single_ranking_keeps_order(self):
        result = ranking.reciprocal_rank_fusion([[5, 3, 9]])
        self.assertEqual([candidate_id for candidate_id, _ in result], [5, 3, 9])

    def test_rrf_one_empty_ranking(self):
        result = ranking.reciprocal_rank_fusion([[4, 2], []])
        self.assertEqual([candidate_id for candidate_id, _ in result], [4, 2])

    def test_rrf_no_rankings(self):
        self.assertEqual(ranking.reciprocal_rank_fusion([]), [])

    def test_rrf_ties_keep_lower_id(self):
        result = ranking.reciprocal_rank_fusion([[2, 1], [1, 2]])
        self.assertEqual([candidate_id for candidate_id, _ in result], [1, 2])

    def test_rrf_negative_constant(self):
        with self.assertRaises(ValueError):
            ranking.reciprocal_rank_fusion([[1]], k_rrf=-1)


class TestNormalizeScores(unittest.TestCase):
    def test_normalize_example(self):
        self.assertEqual(ranking.normalize_scores([2.0, 4.0, 3.0]), [0.0, 1.0, 0.5])

    def test_normalize_all_equal(self):
        self.assertEqual(ranking.normalize_scores([0.3, 0.3]), [1.0, 1.0])

    def test_normalize_empty(self):
        self.assertEqual(ranking.normalize_scores([]), [])
