import pytest

from captchamonitor.fetchers.firefox_browser import FirefoxBrowser


class TestFirefoxBrowser:
    @classmethod
    def setup_class(cls):
        cls.target_url = "https://check.torproject.org/"

    def test_firefox_browser_without_tor(self, config):
        firefox_browser = FirefoxBrowser(
            config=config,
            url=self.target_url,
        )

        firefox_browser.setup()
        firefox_browser.connect()
        firefox_browser.fetch()

        assert "Sorry. You are not using Tor." in firefox_browser.page_source

        firefox_browser.close()

    def test_firefox_browser_with_tor(self, config, tor_proxy):
        firefox_browser = FirefoxBrowser(
            config=config,
            url=self.target_url,
            proxy=tor_proxy,
            use_proxy_type="tor",
        )

        firefox_browser.setup()
        firefox_browser.connect()
        firefox_browser.fetch()

        assert (
            "Congratulations. This browser is configured to use Tor."
            in firefox_browser.page_source
        )

        firefox_browser.close()

    @pytest.mark.flaky(reruns=0)
    def test_firefox_browser_with_http_proxy(self, config, http_proxy):
        firefox_browser = FirefoxBrowser(
            config=config,
            url=self.target_url,
            proxy=http_proxy,
            use_proxy_type="http",
        )

        firefox_browser.setup()
        firefox_browser.connect()
        firefox_browser.fetch()

        assert http_proxy[0] in firefox_browser.page_source

        firefox_browser.close()
