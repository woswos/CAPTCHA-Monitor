import pytest

from captchamonitor.fetchers.chrome_browser import ChromeBrowser


class TestChromeBrowser:
    @classmethod
    def setup_class(cls):
        cls.target_url = "https://check.torproject.org/"

    def test_chrome_browser_without_tor(self, config):
        chrome_browser = ChromeBrowser(
            config=config,
            url=self.target_url,
        )

        chrome_browser.setup()
        chrome_browser.connect()
        chrome_browser.fetch()

        assert "Sorry. You are not using Tor." in chrome_browser.page_source

        chrome_browser.close()

    def test_chrome_browser_with_tor(self, config, tor_proxy):
        chrome_browser = ChromeBrowser(
            config=config,
            url=self.target_url,
            proxy=tor_proxy,
            use_proxy_type="tor",
        )

        chrome_browser.setup()
        chrome_browser.connect()
        chrome_browser.fetch()

        assert (
            "Congratulations. This browser is configured to use Tor."
            in chrome_browser.page_source
        )

        chrome_browser.close()

    @pytest.mark.flaky(reruns=0)
    def test_chrome_browser_with_http_proxy(self, config, http_proxy):
        chrome_browser = ChromeBrowser(
            config=config,
            url=self.target_url,
            proxy=http_proxy,
            use_proxy_type="http",
        )

        chrome_browser.setup()
        chrome_browser.connect()
        chrome_browser.fetch()

        assert http_proxy[0] in chrome_browser.page_source

        chrome_browser.close()
