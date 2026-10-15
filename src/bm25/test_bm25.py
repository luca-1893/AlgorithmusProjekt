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
