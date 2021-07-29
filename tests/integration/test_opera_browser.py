# pylint: disable=C0115,C0116,W0212

import pytest

from captchamonitor.fetchers.opera_browser import OperaBrowser


class TestOperaBrowser:
    @classmethod
    def setup_class(cls):
        cls.target_url = "https://check.torproject.org/"

    def test_opera_browser_without_tor(self, config):
        opera_browser = OperaBrowser(
            config=config,
            url=self.target_url,
            explicit_wait_duration=0,
        )

        opera_browser.setup()
        opera_browser.connect()
        opera_browser.fetch()

        assert "Sorry. You are not using Tor." in opera_browser.page_source

        opera_browser.close()

    def test_opera_browser_with_tor(self, config, tor_proxy):
        opera_browser = OperaBrowser(
            config=config,
            url=self.target_url,
            proxy=tor_proxy,
            use_proxy_type="tor",
            explicit_wait_duration=0,
        )

        opera_browser.setup()
        opera_browser.connect()
        opera_browser.fetch()

        assert (
            "Congratulations. This browser is configured to use Tor."
            in opera_browser.page_source
        )

        opera_browser.close()

    @pytest.mark.flaky(reruns=0)
    def test_opera_browser_with_http_proxy(self, config, http_proxy):
        opera_browser = OperaBrowser(
            config=config,
            url=self.target_url,
            proxy=http_proxy,
            use_proxy_type="http",
            explicit_wait_duration=0,
        )

        opera_browser.setup()
        opera_browser.connect()
        opera_browser.fetch()

        assert http_proxy[0] in opera_browser.page_source

        opera_browser.close()
