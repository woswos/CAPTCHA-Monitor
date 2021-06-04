import unittest

import pytest

from captchamonitor.utils.website_parser import WebsiteParser


class TestWebsiteParser(unittest.TestCase):
    def setUp(self):
        self.valid_website_alexa = "http://baidu.com"
        self.invalid_website_alexa = "http://www.ogl.com"
        self.get_alexa_top_50_number = 50

        self.valid_website_moz = "http://google.com"
        self.invalid_website_moz = "http://www.ogl.com"
        self.get_moz_top_500_number = 500

        self.get_total_website_number = 550

    def test_get_alexa_top_50(self):
        website = WebsiteParser()
        website.get_alexa_top_50()
        self.assertEqual(website.number_of_websites, self.get_alexa_top_50_number)
        self.assertIn(self.valid_website_alexa, website.website_list)

    def test_get_moz_top_500(self):
        website = WebsiteParser()
        website.get_moz_top_500()
        self.assertEqual(website.number_of_websites, self.get_moz_top_500_number)
        self.assertIn(self.valid_website_moz, website.website_list)

    def test_get_all_website(self):
        website = WebsiteParser()
        website.get_alexa_top_50()
        website.get_moz_top_500()
        self.assertEqual(website.number_of_websites, self.get_total_website_number)
        self.assertIn(self.valid_website_moz, website.uniq_website_list)
        self.assertIn(self.valid_website_alexa, website.uniq_website_list)
        self.assertTrue(len(website.uniq_website_list) >= 500)
