import unittest

from selenium.common.exceptions import TimeoutException

from captchamonitor.utils.config import Config
from captchamonitor.utils.tor_launcher import TorLauncher
from captchamonitor.fetchers.firefox_browser import FirefoxBrowser


class TestGdprRemover(unittest.TestCase):
    def setUp(self):
        self.config = Config()
        self.tor_launcher = TorLauncher(self.config)
        self.target_url = "https://yahoo.com"
        self.exit_relay_in_france = "E2A3EF73F2B26BC4ABB4A2429180897C21DB7BDD"
        self.gdpr_keywords = [
            "Souhlasím",
            "Alle akzeptieren",
            "Jag godkänner",
            "Ich stimme zu",
            "Ik ga akkoord",
            "Godta alle",
            "Egyetértek",
            "J'accepte",
            "I agree",
            "Acceptai tot",
            "Accept all",
            "Accept",
            "Tout accepter",
        ]
        # Connect to an exit node in France
        self.tor_launcher.create_new_circuit_to(self.exit_relay_in_france)

    def test_gdpr_remover(self):
        firefox_browser = FirefoxBrowser(
            config=self.config,
            url=self.target_url,
            tor_launcher=self.tor_launcher,
            options={
                "gdpr_remove": True,
                "gdpr_wait_for_url_change": True,
                "gdpr_keywords": self.gdpr_keywords,
            },
            use_tor=True,
        )

        firefox_browser.setup()
        firefox_browser.connect()
        firefox_browser.fetch()

        driver_url = firefox_browser.driver.current_url

        self.assertNotIn("consent.yahoo.com", driver_url)
        self.assertIn("fr.yahoo.com", driver_url)

        for keyword in self.gdpr_keywords:
            self.assertNotIn(keyword, firefox_browser.page_source)

        firefox_browser.close()

    def test_gdpr_remover_without_keywords(self):
        firefox_browser = FirefoxBrowser(
            config=self.config,
            url=self.target_url,
            tor_launcher=self.tor_launcher,
            options={
                "gdpr_remove": True,
                "gdpr_wait_for_url_change": True,
                "url_change_timeout": 10,
            },
            use_tor=True,
        )

        firefox_browser.setup()
        firefox_browser.connect()

        # It should timeout because we asked the fetcher to wait until the url
        # changes, but the URL never changes since we didn't click on anything.
        # We didn't click on anything, because we didn't pass any keywords.
        with self.assertRaises(TimeoutException):
            firefox_browser.fetch()

        firefox_browser.close()
