import unittest
import bm25

class test_bm25(unittest.TestCase):
    def tokenizer_example(self):
        self.assertEqual(tokenizer("DEr  Apfel-Baum ist grün."), ["der", "apfel", "baum", "ist", "grün"])
    def tokenizer_empty_String(self):
        self.assertEqual(tokenizer(" "), [])
    def tokenizer_only_punctuation(self):
        self.assertEqual(tokenizer(".!?"), [])


