import unittest

import pytest

from captchamonitor.utils.config import Config
from captchamonitor.utils.tor_launcher import TorLauncher
from captchamonitor.utils.small_scripts import get_random_http_proxy
from captchamonitor.fetchers.opera_browser import OperaBrowser


class TestOperaBrowser(unittest.TestCase):
    def setUp(self):
        self.config = Config()
        self.target_url = "https://check.torproject.org/"

    def test_opera_browser_without_tor(self):
        opera_browser = OperaBrowser(
            config=self.config,
            url=self.target_url,
        )

        opera_browser.setup()
        opera_browser.connect()
        opera_browser.fetch()

        self.assertIn("Sorry. You are not using Tor.", opera_browser.page_source)

        opera_browser.close()

    def test_opera_browser_with_tor(self):
        tor_launcher = TorLauncher(self.config)
        proxy = (
            tor_launcher.ip_address,
            tor_launcher.socks_port,
        )

        opera_browser = OperaBrowser(
            config=self.config,
            url=self.target_url,
            proxy=proxy,
            use_proxy_type="tor",
        )

        opera_browser.setup()
        opera_browser.connect()
        opera_browser.fetch()

        self.assertIn(
            "Congratulations. This browser is configured to use Tor.",
            opera_browser.page_source,
        )

        opera_browser.close()

    @pytest.mark.flaky(reruns=0)
    def test_opera_browser_with_http_proxy(self):
        proxy = get_random_http_proxy()

        opera_browser = OperaBrowser(
            config=self.config,
            url=self.target_url,
            proxy=proxy,
            use_proxy_type="http",
        )

        opera_browser.setup()
        opera_browser.connect()
        opera_browser.fetch()

        self.assertIn(
            proxy[0],
            opera_browser.page_source,
        )

        opera_browser.close()
