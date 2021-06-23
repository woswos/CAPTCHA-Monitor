import unittest

from captchamonitor.utils.website_parser import WebsiteParser


class TestWebsiteParser(unittest.TestCase):
    def setUp(self):
        self.valid_website_alexa = "baidu.com"
        self.invalid_website_alexa = "ogl.com"

        self.valid_website_moz = "google.com"
        self.invalid_website_moz = "ogl.com"

    def test_get_alexa_top_50(self):
        website = WebsiteParser()
        website.get_alexa_top_50()

        self.assertEqual(
            website.number_of_websites,
            50,
            "Parser should have returned 50 websites",
        )
        self.assertIn(self.valid_website_alexa, website.website_list)

        self.assertNotIn(self.invalid_website_alexa, website.website_list)

    def test_get_moz_top_500(self):
        website = WebsiteParser()
        website.get_moz_top_500()

        self.assertEqual(
            website.number_of_websites,
            500,
            "Parser should have returned 500 websites",
        )
        self.assertIn(self.valid_website_moz, website.website_list)

        self.assertNotIn(self.invalid_website_moz, website.website_list)

    def test_get_all_website(self):
        website = WebsiteParser()
        website.get_alexa_top_50()
        website.get_moz_top_500()

        self.assertEqual(
            website.number_of_websites,
            550,
            "Parser should have returned 550 websites",
        )

        self.assertIn(self.valid_website_moz, website.unique_website_list)
        self.assertIn(self.valid_website_alexa, website.unique_website_list)

        self.assertGreaterEqual(len(website.unique_website_list), 500)
        self.assertLessEqual(len(website.unique_website_list), 550)

        self.assertNotIn(self.invalid_website_alexa, website.website_list)
        self.assertNotIn(self.invalid_website_moz, website.website_list)
