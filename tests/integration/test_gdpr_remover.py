# pylint: disable=C0115,C0116,W0212,W0702

import pytest
from selenium.common.exceptions import TimeoutException

from captchamonitor.utils.small_scripts import get_random_exit_relay
from captchamonitor.fetchers.firefox_browser import FirefoxBrowser


@pytest.mark.flaky(reruns=0)
@pytest.mark.parametrize(
    "tor_proxy_to_relay",
    [get_random_exit_relay(country="DE", multiple=True)[:5]],
    indirect=True,
)
class TestGdprRemover:
    @classmethod
    def setup_class(cls):
        cls.target_url = "https://yahoo.com"

    def test_gdpr_remover(self, config, tor_proxy_to_relay, gdpr_keywords):
        firefox_browser = FirefoxBrowser(
            config=config,
            url=self.target_url,
            proxy=tor_proxy_to_relay,
            use_proxy_type="tor",
            options={
                "gdpr_remove": True,
                "gdpr_wait_for_url_change": True,
                "gdpr_keywords": gdpr_keywords,
            },
        )

        firefox_browser.setup()
        firefox_browser.connect()
        firefox_browser.fetch()

        driver_url = firefox_browser.driver.current_url

        assert "consent.yahoo.com" not in driver_url
        assert "de.yahoo.com" in driver_url

        for keyword in gdpr_keywords:
            assert keyword not in firefox_browser.page_source

        firefox_browser.close()

    def test_gdpr_remover_without_keywords(self, config, tor_proxy_to_relay):
        firefox_browser = FirefoxBrowser(
            config=config,
            url=self.target_url,
            proxy=tor_proxy_to_relay,
            use_proxy_type="tor",
            options={
                "gdpr_remove": True,
                "gdpr_wait_for_url_change": True,
                "url_change_timeout": 10,
            },
        )

        firefox_browser.setup()
        firefox_browser.connect()

        # It should timeout because we asked the fetcher to wait until the url
        # changes, but the URL never changes since we didn't click on anything.
        # We didn't click on anything, because we didn't pass any keywords.
        with pytest.raises(TimeoutException):
            firefox_browser.fetch()

        firefox_browser.close()
