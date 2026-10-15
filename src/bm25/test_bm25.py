import math
import unittest

import bm25


class TestTokenize(unittest.TestCase):
    def test_tokenize_apostrophe(self):
        self.assertEqual(bm25.tokenize("don't"), ["dont"])

    def test_tokenize_casefold_eszett(self):
        self.assertEqual(bm25.tokenize("Straße"), ["strasse"])

    def test_tokenize_em_dash(self):
        self.assertEqual(bm25.tokenize("kam—und"), ["kam", "und"])

    def test_tokenize_empty_string(self):
        self.assertEqual(bm25.tokenize(""), [])

    def test_tokenize_en_dash_range(self):
        self.assertEqual(bm25.tokenize("Seiten 10–20"), ["seiten", "10", "20"])

    def test_tokenize_example(self):
        self.assertEqual(bm25.tokenize("DEr  Apfel-Baum ist grün."), ["der", "apfelbaum", "ist", "grün"])

    def test_tokenize_inner_dash(self):
        self.assertEqual(bm25.tokenize("Apfel–Baum"), ["apfel", "baum"])

    def test_tokenize_inner_hyphen(self):
        self.assertEqual(bm25.tokenize("E-Mail"), ["email"])

    def test_tokenize_letter_digit_hyphen(self):
        self.assertEqual(bm25.tokenize("COVID-19"), ["covid19"])

    def test_tokenize_only_hyphens(self):
        self.assertEqual(bm25.tokenize("- -- ---"), [])

    def test_tokenize_only_punctuation(self):
        self.assertEqual(bm25.tokenize(".!?"), [])

    def test_tokenize_only_whitespace(self):
        self.assertEqual(bm25.tokenize("   "), [])

    def test_tokenize_single_quotes(self):
        self.assertEqual(bm25.tokenize("'Apfel'"), ["apfel"])

    def test_tokenize_standalone_dash(self):
        self.assertEqual(bm25.tokenize("Apfel – Baum"), ["apfel", "baum"])

    def test_tokenize_standalone_hyphen(self):
        self.assertEqual(bm25.tokenize("Wort - Wort"), ["wort", "wort"])

    def test_tokenize_trailing_hyphen(self):
        self.assertEqual(bm25.tokenize("Vor- und Nachteile"), ["vor", "und", "nachteile"])

    def test_tokenize_typographic_apostrophe(self):
        self.assertEqual(bm25.tokenize("don’t"), ["dont"])


class TestBuildIndex(unittest.TestCase):
    def test_build_index_avgdl(self):
        _, _, n_docs, avgdl = bm25.build_index(["a b c", "", "a b c d e f g"])
        self.assertEqual(n_docs, 2)
        self.assertAlmostEqual(avgdl, 5.0)
        self.assertIsInstance(avgdl, float)

    def test_build_index_casefold_merges_terms(self):
        index, _, _, _ = bm25.build_index(["Dog DOG dOg", "Straße STRASSE"])
        self.assertEqual(index["dog"], {0: 3})
        self.assertEqual(index["strasse"], {1: 2})
        self.assertNotIn("Dog", index)

    def test_build_index_does_not_mutate_corpus(self):
        corpus = ["dog", "", "cat"]
        original = list(corpus)
        bm25.build_index(corpus)
        self.assertEqual(corpus, original)

    def test_build_index_empty_corpus(self):
        self.assertEqual(bm25.build_index([]), ({}, {}, 0, 0.0))

    def test_build_index_example(self):
        corpus = ["Apfel apfel Banane.", "Banane, Milch!", ".!?", "Apfel Brot Milch Käse Butter"]
        index, doc_lengths, n_docs, avgdl = bm25.build_index(corpus)

        self.assertEqual(index["apfel"], {0: 2, 3: 1})
        self.assertEqual(index["milch"], {1: 1, 3: 1})
        self.assertEqual(doc_lengths, {0: 3, 1: 2, 3: 5})
        self.assertEqual(n_docs, 3)
        self.assertAlmostEqual(avgdl, 10 / 3)

    def test_build_index_identical_documents_get_separate_ids(self):
        index, _, n_docs, _ = bm25.build_index(["dog", "dog"])
        self.assertEqual(index["dog"], {0: 1, 1: 1})
        self.assertEqual(n_docs, 2)

    def test_build_index_invariants(self):
        corpus = ["The dog barks.", "", "The dog and the cat, the dog!", "..."]
        index, doc_lengths, n_docs, _ = bm25.build_index(corpus)

        for doc_id, length in doc_lengths.items():
            self.assertEqual(sum(p.get(doc_id, 0) for p in index.values()), length)

        for posting in index.values():
            self.assertLessEqual(set(posting), set(doc_lengths))
            self.assertTrue(1 <= len(posting) <= n_docs)
            self.assertTrue(all(tf >= 1 for tf in posting.values()))

    def test_build_index_joiner_variants_merge(self):
        index, doc_lengths, _, _ = bm25.build_index(["E-Mail email e’mail"])
        self.assertEqual(index, {"email": {0: 3}})
        self.assertEqual(doc_lengths[0], 3)

    def test_build_index_only_empty_documents(self):
        for corpus in ([""], ["   "], [".!?"], ["- -- ---"], ["", "\n\t", "?"]):
            with self.subTest(corpus=corpus):
                index, doc_lengths, n_docs, avgdl = bm25.build_index(corpus)
                self.assertEqual(index, {})
                self.assertEqual(doc_lengths, {})
                self.assertEqual(n_docs, 0)
                self.assertEqual(avgdl, 0.0)

    def test_build_index_stable_ids_with_empty_document(self):
        index, doc_lengths, n_docs, _ = bm25.build_index(["dog", "", "cat"])
        self.assertEqual(doc_lengths, {0: 1, 2: 1})
        self.assertEqual(index["cat"], {2: 1})
        self.assertEqual(n_docs, 2)

    def test_build_index_term_frequency(self):
        index, doc_lengths, _, _ = bm25.build_index(["dog dog dog cat"])
        self.assertEqual(index["dog"], {0: 3})
        self.assertEqual(index["cat"], {0: 1})
        self.assertEqual(doc_lengths[0], 4)

class TestIDF(unittest.TestCase):

    def test_compute_idf_known_values(self):
        cases = [
            (0, 3, math.log(8)),  # unknown term
            (1, 3, math.log(8 / 3)),
            (2, 3, math.log(8 / 5)),  # "apfel", "milch" in example corpus → ≈ 0.470
            (3, 3, math.log(8 / 7)),  # term in every doc
        ]
        for df, n_docs, expected in cases:
            with self.subTest(df=df, n_docs=n_docs):
                self.assertAlmostEqual(bm25.compute_idf(df, n_docs), expected)

    def test_compute_idf_always_positive(self):
        for n_docs in range(0, 20):
            for df in range(0, n_docs + 1):
                with self.subTest(df=df, n_docs=n_docs):
                    self.assertGreater(bm25.compute_idf(df, n_docs), 0)

    def test_compute_idf_decreases_with_df(self):
        n_docs = 10
        idfs = [bm25.compute_idf(df, n_docs) for df in range(n_docs + 1)]
        for rarer, more_common in zip(idfs, idfs[1:]):
            self.assertGreater(rarer, more_common)


class TestScore(unittest.TestCase):
    def setUp(self):
        corpus = ["Apfel apfel Banane.", "Banane, Milch!", ".!?", "Apfel Brot Milch Käse Butter"]
        self.index, self.doc_lengths, self.n_docs, self.avgdl = bm25.build_index(corpus)
        self.query = {"apfel", "milch"}

    def _score(self, doc_id):
        return bm25.compute_score(self.query, doc_id, self.index, self.doc_lengths, self.n_docs, self.avgdl)

    def test_score_reference_values(self):
        for doc_id, expected in [(0, 0.694), (1, 0.573), (2, 0.0), (3, 0.767)]:
            with self.subTest(doc_id=doc_id):
                self.assertAlmostEqual(self._score(doc_id), expected, places=3)

    def test_term_score_zero_frequency(self):
        self.assertEqual(bm25.compute_term_score(0, 3, 10 / 3, 0.47, 1.5, 0.75), 0.0)

    def test_score_unknown_terms(self):
        self.assertEqual(bm25.compute_score({"xyz"}, 0, self.index, self.doc_lengths, self.n_docs, self.avgdl), 0.0)

    def test_score_unknown_term_does_not_change_score(self):
        with_unknown = bm25.compute_score(self.query | {"pizza"}, 3, self.index, self.doc_lengths,
                                          self.n_docs, self.avgdl)
        self.assertAlmostEqual(with_unknown, self._score(3))

    def test_score_empty_index(self):
        self.assertEqual(bm25.compute_score({"apfel"}, 0, {}, {}, 0, 0.0), 0.0)

    def test_score_unknown_doc_id(self):
        self.assertEqual(
            bm25.compute_score(self.query, 99, self.index, self.doc_lengths, self.n_docs, self.avgdl),
            0.0,
        )
