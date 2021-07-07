# pylint: disable=C0115,C0116,W0212

from captchamonitor.utils.website_parser import WebsiteParser


class TestWebsiteParser:
    @classmethod
    def setup_class(cls):
        cls.valid_website_alexa = "baidu.com"
        cls.invalid_website_alexa = "ogl.com"

        cls.valid_website_moz = "google.com"
        cls.invalid_website_moz = "ogl.com"

    def test_get_alexa_top_50(self):
        website = WebsiteParser()
        website.get_alexa_top_50()

        assert website.number_of_websites == 50
        assert self.valid_website_alexa in website.website_list

        assert self.invalid_website_alexa not in website.website_list

    def test_get_moz_top_500(self):
        website = WebsiteParser()
        website.get_moz_top_500()

        assert website.number_of_websites == 500
        assert self.valid_website_moz in website.website_list

        assert self.invalid_website_moz not in website.website_list

    def test_get_all_website(self):
        website = WebsiteParser()
        website.get_alexa_top_50()
        website.get_moz_top_500()

        assert website.number_of_websites == 550

        assert self.valid_website_moz in website.unique_website_list
        assert self.valid_website_alexa in website.unique_website_list

        assert len(website.unique_website_list) >= 500
        assert len(website.unique_website_list) <= 550

        assert self.invalid_website_alexa not in website.website_list
        assert self.invalid_website_moz not in website.website_list
