import unittest
from text_processing import normalize_html_content


class TestNormalizeHTMLContent(unittest.TestCase):
    def test_normalize_whitespace(self):
        self.assertEqual(
            normalize_html_content("This   is  a   test"), "This is a test"
        )

    def test_remove_html_tags(self):
        self.assertEqual(normalize_html_content("<p>Test</p>"), "Test")

    def test_remove_urls(self):
        self.assertEqual(normalize_html_content("Visit http://example.com"), "Visit")

    def test_remove_html_and_urls(self):
        self.assertEqual(
            normalize_html_content("<p>Visit http://example.com</p>"), "Visit"
        )

    def test_fix_encoding(self):
        self.assertEqual(normalize_html_content("Café"), "Caf")

    def test_combined_cases(self):
        self.assertEqual(
            normalize_html_content("<p>Visit http://example.com for more info</p>"),
            "Visit for more info",
        )


if __name__ == "__main__":
    unittest.main()
