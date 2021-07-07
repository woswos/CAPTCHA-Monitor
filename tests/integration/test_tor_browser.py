# pylint: disable=C0115,C0116,W0212

import pytest

from captchamonitor.utils.exceptions import TorBrowserProfileLocationError
from captchamonitor.utils.small_scripts import deep_copy
from captchamonitor.fetchers.tor_browser import TorBrowser


class TestTorBrowser:
    @classmethod
    def setup_class(cls):
        cls.target_url = "https://check.torproject.org/"

    def test_tor_browser_security_level_standard(self, config, tor_proxy):
        tor_browser = TorBrowser(
            config=config,
            url=self.target_url,
            proxy=tor_proxy,
            use_proxy_type="tor",
            options={"tbb_security_level": "standard"},
        )

        tor_browser.setup()
        tor_browser.connect()
        tor_browser.fetch()

        assert (
            "Congratulations. This browser is configured to use Tor."
            in tor_browser.page_source
        )

        tor_browser.close()

    def test_tor_browser_wrong_profile_location(self, config, tor_proxy):
        test_config = deep_copy(config)

        # Modify the profile directory
        test_config[
            "docker_tor_browser_container_profile_location"
        ] = "obviously_wrong_directory"

        tor_browser = TorBrowser(
            config=test_config,
            url=self.target_url,
            proxy=tor_proxy,
            use_proxy_type="tor",
            options={"tbb_security_level": "standard"},
        )

        # Check if the exception is correct
        with pytest.raises(TorBrowserProfileLocationError):
            tor_browser.setup()

    def test_tor_browser_with_wrong_security_option(self, config, tor_proxy):
        tor_browser = TorBrowser(
            config=config,
            url=self.target_url,
            proxy=tor_proxy,
            use_proxy_type="tor",
            options={"tbb_security_level": None},
        )

        # Try to setup the browser
        tor_browser.setup()

    def test_tor_browser_with_no_option(self, config, tor_proxy):
        tor_browser = TorBrowser(
            config=config,
            url=self.target_url,
            proxy=tor_proxy,
            use_proxy_type="tor",
        )

        # Try to setup the browser
        tor_browser.setup()

    def test_tor_browser_security_level_safer(self, config, tor_proxy):
        tor_browser = TorBrowser(
            config=config,
            url=self.target_url,
            proxy=tor_proxy,
            use_proxy_type="tor",
            options={"tbb_security_level": "safer"},
        )

        tor_browser.setup()
        tor_browser.connect()
        tor_browser.fetch()

        assert (
            "Congratulations. This browser is configured to use Tor."
            in tor_browser.page_source
        )

        tor_browser.close()

    @pytest.mark.skip(
        reason="HAR exporting doesn't work in safest mode since JS is blocked completely"
    )
    def test_tor_browser_security_level_safest(self, config, tor_proxy):
        tor_browser = TorBrowser(
            config=config,
            url=self.target_url,
            proxy=tor_proxy,
            use_proxy_type="tor",
            options={"tbb_security_level": "safest"},
        )

        tor_browser.setup()
        tor_browser.connect()
        tor_browser.fetch()

        assert (
            "Congratulations. This browser is configured to use Tor."
            in tor_browser.page_source
        )

        tor_browser.close()

    @pytest.mark.flaky(reruns=0)
    def test_tor_browser_with_http_proxy(self, config, http_proxy):
        tor_browser = TorBrowser(
            config=config,
            url=self.target_url,
            proxy=http_proxy,
            use_proxy_type="http",
        )

        tor_browser.setup()
        tor_browser.connect()
        tor_browser.fetch()

        assert http_proxy[0] in tor_browser.page_source

        tor_browser.close()
