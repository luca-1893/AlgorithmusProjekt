import unittest
import bm25

class TestBm25(unittest.TestCase):
    def test_tokenizer_example(self):
        self.assertEqual(bm25.tokenizer("DEr  Apfel-Baum ist grün."), ["der", "apfelbaum", "ist", "grün"])

    def test_tokenizer_lower_edgecase(self):
        self.assertEqual(bm25.tokenizer("Straße"), ["strasse"])

    def test_tokenizer_inner_hyphen(self):
        self.assertEqual(bm25.tokenizer("E-Mail"), ["email"])

    def test_tokenizer_letter_digit_hyphen(self):
        self.assertEqual(bm25.tokenizer("COVID-19"), ["covid19"])

    def test_tokenizer_standalone_hyphen(self):
        self.assertEqual(bm25.tokenizer("Wort - Wort"), ["wort", "wort"])

    def test_tokenizer_trailing_hyphen(self):
        self.assertEqual(bm25.tokenizer("Vor- und Nachteile"), ["vor", "und", "nachteile"])

    def test_tokenizer_only_hyphens(self):
        self.assertEqual(bm25.tokenizer("- -- ---"), [])