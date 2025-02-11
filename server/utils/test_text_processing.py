import unittest
from text_processing import clean_text


class TestCleanText(unittest.TestCase):

    def test_remove_html_tags(self):
        self.assertEqual(clean_text("<p>Test</p>"), "Test")

    def test_remove_urls(self):
        self.assertEqual(clean_text("Visit http://example.com"), "Visit")

    def test_normalize_whitespace(self):
        self.assertEqual(clean_text("This   is  a   test"), "This is a test")

    def test_remove_html_and_urls(self):
        self.assertEqual(clean_text("<p>Visit http://example.com</p>"), "Visit")

    def test_fix_encoding(self):
        self.assertEqual(clean_text("Café"), "Caf")

    def test_combined_cases(self):
        self.assertEqual(
            clean_text("<p>Visit http://example.com for more info</p>"),
            "Visit for more info",
        )


if __name__ == "__main__":
    unittest.main()
