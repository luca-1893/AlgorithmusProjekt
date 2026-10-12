import unittest
import bm25

class TestBM25(unittest.TestCase):
    def test_tokenizer_example(self):
        self.assertEqual(bm25.tokenizer("DEr  Apfel-Baum ist grün."), ["der", "apfel", "baum", "ist", "grün"])
    def test_tokenizer_empty_String(self):
        self.assertEqual(bm25.tokenizer(""), [])
    def test_tokenizer_space_only(self):
        self.assertEqual(bm25.tokenizer(" "), [])
    def test_tokenizer_only_punctuation(self):
        self.assertEqual(bm25.tokenizer(".!?"), [])


