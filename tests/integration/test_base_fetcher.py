import unittest
from random import randint

from captchamonitor.utils.config import Config
from captchamonitor.utils.tor_launcher import TorLauncher
from captchamonitor.fetchers.base_fetcher import BaseFetcher


class TestBaseFetcher(unittest.TestCase):
    def setUp(self):
        self.config = Config()
        self.tor_launcher = TorLauncher(self.config)
        self.target_url = "https://check.torproject.org/"
        self.page_timeout_value = randint(0, 1000)
        self.script_timeout_value = randint(0, 1000)

    def test_base_fetcher_init(self):
        base_fetcher = BaseFetcher(
            config=self.config,
            url=self.target_url,
            tor_launcher=self.tor_launcher,
            use_tor=False,
        )

        self.assertEqual(base_fetcher.page_timeout, 30)
        self.assertEqual(base_fetcher.script_timeout, 30)

    def test_base_fetcher_init_with_options(self):
        base_fetcher_1 = BaseFetcher(
            config=self.config,
            url=self.target_url,
            tor_launcher=self.tor_launcher,
            options={
                "page_timeout": self.page_timeout_value,
                "script_timeout": self.script_timeout_value,
            },
            use_tor=False,
        )

        self.assertEqual(base_fetcher_1.page_timeout, self.page_timeout_value)
        self.assertEqual(base_fetcher_1.script_timeout, self.script_timeout_value)

        base_fetcher_2 = BaseFetcher(
            config=self.config,
            url=self.target_url,
            tor_launcher=self.tor_launcher,
            options={
                "script_timeout": self.script_timeout_value,
            },
            use_tor=False,
        )

        self.assertEqual(base_fetcher_2.page_timeout, 30)
        self.assertEqual(base_fetcher_2.script_timeout, self.script_timeout_value)

        base_fetcher_3 = BaseFetcher(
            config=self.config,
            url=self.target_url,
            tor_launcher=self.tor_launcher,
            options={
                "page_timeout": self.page_timeout_value,
            },
            use_tor=False,
        )

        self.assertEqual(base_fetcher_3.page_timeout, self.page_timeout_value)
        self.assertEqual(base_fetcher_3.script_timeout, 30)
