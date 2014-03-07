import os
import sys
sys.path += [os.path.join(sys.path[0], '..')]
import grammar
import unittest

class GrammarTest(unittest.TestCase):
    def test_camelcase(self):
        self.assertEqual("-".join(grammar.Word("test")), "test")
        self.assertEqual("-".join(grammar.Word("tesT")), "tes-T")
        self.assertEqual("-".join(grammar.Word("teSt")), "te-St")
        self.assertEqual("-".join(grammar.Word("teST")), "te-ST")

        self.assertEqual("-".join(grammar.Word("tEst")), "t-Est")
        self.assertEqual("-".join(grammar.Word("tEsT")), "t-Es-T")
        self.assertEqual("-".join(grammar.Word("tESt")), "t-ESt")
        self.assertEqual("-".join(grammar.Word("tEST")), "t-EST")

        self.assertEqual("-".join(grammar.Word("Test")), "Test")
        self.assertEqual("-".join(grammar.Word("TesT")), "Tes-T")
        self.assertEqual("-".join(grammar.Word("TeSt")), "Te-St")
        self.assertEqual("-".join(grammar.Word("TeST")), "Te-ST")

        self.assertEqual("-".join(grammar.Word("TEst")), "TEst")
        self.assertEqual("-".join(grammar.Word("TEsT")), "TEs-T")
        self.assertEqual("-".join(grammar.Word("TESt")), "TESt")
        self.assertEqual("-".join(grammar.Word("TEST")), "TEST")

    def test_runs(self):
        self.assertEqual("-".join(grammar.Word("whaaaaat")), "whaaaaat")

    def test_url(self):
        sent = grammar.Sentence("a url: http://www.example.com/")
        self.assertEqual(str(sent[0]), "a")
        self.assertEqual(str(sent[1]), "url")
        self.assertEqual(str(sent[2]), "http://www.example.com/")

    def test_unicode(self):
        sent = grammar.Sentence(u"M\xf6tley Cr\xfce")

        self.assertEqual(str(sent), "M\xc3\xb6tley Cr\xc3\xbce")
        self.assertEqual(unicode(sent), u"M\xf6tley Cr\xfce")

        self.assertEqual(u"-".join(grammar.Word(u"M\xf6tley")), u"M\xf6t-ley")

if __name__ == '__main__':
    unittest.main()
