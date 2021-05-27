import pytest
import unittest
from captchamonitor.utils.config import Config
from captchamonitor.utils.tor_launcher import TorLauncher
from captchamonitor.fetchers.tor_browser import TorBrowser


class TestTorBrowser(unittest.TestCase):
    def setUp(self):
        self.config = Config()
        self.tor_launcher = TorLauncher(self.config)
        self.target_url = "https://check.torproject.org/"

    def test_tor_browser_security_level_standard(self):
        tor_browser = TorBrowser(
            config=self.config,
            url=self.target_url,
            tor_launcher=self.tor_launcher,
            options={"TorBrowserSecurityLevel": "standard"},
            use_tor=True,
        )

        tor_browser.setup()
        tor_browser.connect()
        tor_browser.fetch()

        self.assertIn(
            "Congratulations. This browser is configured to use Tor.",
            tor_browser.page_source,
        )

    def test_tor_browser_security_level_safer(self):
        tor_browser = TorBrowser(
            config=self.config,
            url=self.target_url,
            tor_launcher=self.tor_launcher,
            options={"TorBrowserSecurityLevel": "safer"},
            use_tor=True,
        )

        tor_browser.setup()
        tor_browser.connect()
        tor_browser.fetch()

        self.assertIn(
            "Congratulations. This browser is configured to use Tor.",
            tor_browser.page_source,
        )

    @pytest.mark.skip(
        reason="HAR exporting doesn't work in safest mode since JS is blocked completely"
    )
    def test_tor_browser_security_level_safest(self):
        tor_browser = TorBrowser(
            config=self.config,
            url=self.target_url,
            tor_launcher=self.tor_launcher,
            options={"TorBrowserSecurityLevel": "safest"},
            use_tor=True,
        )

        tor_browser.setup()
        tor_browser.connect()
        tor_browser.fetch()

        self.assertIn(
            "Congratulations. This browser is configured to use Tor.",
            tor_browser.page_source,
        )
