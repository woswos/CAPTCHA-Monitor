import unittest

import pytest

from captchamonitor.utils.config import Config
from captchamonitor.utils.exceptions import TorBrowserProfileLocationError
from captchamonitor.utils.tor_launcher import TorLauncher
from captchamonitor.utils.small_scripts import deep_copy, get_random_http_proxy
from captchamonitor.fetchers.tor_browser import TorBrowser


class TestTorBrowser(unittest.TestCase):
    def setUp(self):
        self.config = Config()
        self.tor_launcher = TorLauncher(self.config)
        self.proxy = (
            self.tor_launcher.ip_address,
            self.tor_launcher.socks_port,
        )
        self.target_url = "https://check.torproject.org/"

    def test_tor_browser_security_level_standard(self):
        tor_browser = TorBrowser(
            config=self.config,
            url=self.target_url,
            proxy=self.proxy,
            use_proxy_type="tor",
            options={"tbb_security_level": "standard"},
        )

        tor_browser.setup()
        tor_browser.connect()
        tor_browser.fetch()

        self.assertIn(
            "Congratulations. This browser is configured to use Tor.",
            tor_browser.page_source,
        )

        tor_browser.close()

    def test_tor_browser_wrong_profile_location(self):
        test_config = deep_copy(self.config)

        # Modify the profile directory
        test_config[
            "docker_tor_browser_container_profile_location"
        ] = "obviously_wrong_directory"

        tor_browser = TorBrowser(
            config=test_config,
            url=self.target_url,
            proxy=self.proxy,
            use_proxy_type="tor",
            options={"tbb_security_level": "standard"},
        )

        # Try to setup the browser
        with pytest.raises(TorBrowserProfileLocationError) as pytest_wrapped_e:
            tor_browser.setup()

        # Check if the exception is correct
        self.assertEqual(pytest_wrapped_e.type, TorBrowserProfileLocationError)

    def test_tor_browser_with_wrong_security_option(self):
        tor_browser = TorBrowser(
            config=self.config,
            url=self.target_url,
            proxy=self.proxy,
            use_proxy_type="tor",
            options={"tbb_security_level": None},
        )

        # Try to setup the browser
        tor_browser.setup()

    def test_tor_browser_with_no_option(self):
        tor_browser = TorBrowser(
            config=self.config,
            url=self.target_url,
            proxy=self.proxy,
            use_proxy_type="tor",
        )

        # Try to setup the browser
        tor_browser.setup()

    def test_tor_browser_security_level_safer(self):
        tor_browser = TorBrowser(
            config=self.config,
            url=self.target_url,
            proxy=self.proxy,
            use_proxy_type="tor",
            options={"tbb_security_level": "safer"},
        )

        tor_browser.setup()
        tor_browser.connect()
        tor_browser.fetch()

        self.assertIn(
            "Congratulations. This browser is configured to use Tor.",
            tor_browser.page_source,
        )

        tor_browser.close()

    @pytest.mark.skip(
        reason="HAR exporting doesn't work in safest mode since JS is blocked completely"
    )
    def test_tor_browser_security_level_safest(self):
        tor_browser = TorBrowser(
            config=self.config,
            url=self.target_url,
            proxy=self.proxy,
            use_proxy_type="tor",
            options={"tbb_security_level": "safest"},
        )

        tor_browser.setup()
        tor_browser.connect()
        tor_browser.fetch()

        self.assertIn(
            "Congratulations. This browser is configured to use Tor.",
            tor_browser.page_source,
        )

        tor_browser.close()

    @pytest.mark.flaky(reruns=0)
    def test_tor_browser_with_http_proxy(self):
        proxy = get_random_http_proxy()

        tor_browser = TorBrowser(
            config=self.config,
            url=self.target_url,
            proxy=proxy,
            use_proxy_type="http",
        )

        tor_browser.setup()
        tor_browser.connect()
        tor_browser.fetch()

        self.assertIn(
            proxy[0],
            tor_browser.page_source,
        )

        tor_browser.close()
