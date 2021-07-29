# pylint: disable=C0115,C0116,W0212,W0702

import pytest

from captchamonitor.utils.small_scripts import get_random_exit_relay
from captchamonitor.fetchers.chrome_browser import ChromeBrowser
from captchamonitor.fetchers.firefox_browser import FirefoxBrowser


@pytest.mark.flaky(reruns=0)
@pytest.mark.parametrize(
    "tor_proxy_to_relay",
    [get_random_exit_relay(country="DE", multiple=True)[:10]],
    indirect=True,
)
class TestGdprRemover:
    @staticmethod
    def test_gdpr_remover_extension_firefox(config, tor_proxy_to_relay):
        firefox_browser = FirefoxBrowser(
            config=config,
            url="https://yahoo.com",
            proxy=tor_proxy_to_relay,
            use_proxy_type="tor",
            export_har=False,
        )

        firefox_browser.setup()
        firefox_browser.connect()
        firefox_browser.fetch()

        driver_url = firefox_browser.driver.current_url

        assert "consent.yahoo.com" not in driver_url
        assert "de.yahoo.com" in driver_url

        firefox_browser.close()

    @staticmethod
    def test_gdpr_remover_extension_chrome(config, tor_proxy_to_relay):
        chrome_browser = ChromeBrowser(
            config=config,
            url="https://youtube.com",
            proxy=tor_proxy_to_relay,
            use_proxy_type="tor",
            export_har=False,
        )

        chrome_browser.setup()
        chrome_browser.connect()
        chrome_browser.fetch()

        driver_url = chrome_browser.driver.current_url

        assert "consent.youtube.com" not in driver_url
        assert "youtube.com" in driver_url

        chrome_browser.close()
