import unittest
import bm25

class TestBM25(unittest.TestCase):
    def test_tokenize_example(self):
        self.assertEqual(bm25.tokenize("DEr  Apfel-Baum ist grün."), ["der", "apfelbaum", "ist", "grün"])

    def test_tokenize_casefold_eszett(self):
        self.assertEqual(bm25.tokenize("Straße"), ["strasse"])

    def test_tokenize_empty_string(self):
        self.assertEqual(bm25.tokenize(""), [])

    def test_tokenize_only_whitespace(self):
        self.assertEqual(bm25.tokenize("   "), [])

    def test_tokenize_only_punctuation(self):
        self.assertEqual(bm25.tokenize(".!?"), [])

    def test_tokenize_inner_hyphen(self):
        self.assertEqual(bm25.tokenize("E-Mail"), ["email"])

    def test_tokenize_letter_digit_hyphen(self):
        self.assertEqual(bm25.tokenize("COVID-19"), ["covid19"])

    def test_tokenize_standalone_hyphen(self):
        self.assertEqual(bm25.tokenize("Wort - Wort"), ["wort", "wort"])

    def test_tokenize_trailing_hyphen(self):
        self.assertEqual(bm25.tokenize("Vor- und Nachteile"), ["vor", "und", "nachteile"])

    def test_tokenize_only_hyphens(self):
        self.assertEqual(bm25.tokenize("- -- ---"), [])

    def test_tokenize_inner_dash(self):
        self.assertEqual(bm25.tokenize("Apfel–Baum"), ["apfelbaum"])

    def test_tokenize_standalone_dash(self):
        self.assertEqual(bm25.tokenize("Apfel – Baum"), ["apfel", "baum"])

    def test_tokenize_apostrophe(self):
        self.assertEqual(bm25.tokenize("don't"), ["dont"])

    def test_tokenize_typographic_apostrophe(self):
        self.assertEqual(bm25.tokenize("don’t"), ["dont"])

    def test_tokenize_single_quotes(self):
        self.assertEqual(bm25.tokenize("'Apfel'"), ["apfel"])
