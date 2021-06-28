from random import randint

from captchamonitor.fetchers.base_fetcher import BaseFetcher


class TestBaseFetcher:
    @classmethod
    def setup_class(cls):
        cls.target_url = "https://check.torproject.org/"
        cls.page_timeout_value = randint(0, 1000)
        cls.script_timeout_value = randint(0, 1000)

    def test_base_fetcher_init(self, config):
        base_fetcher = BaseFetcher(
            config=config,
            url=self.target_url,
        )

        assert base_fetcher.page_timeout == 30
        assert base_fetcher.script_timeout == 30

    def test_base_fetcher_init_with_options(self, config):
        base_fetcher_1 = BaseFetcher(
            config=config,
            url=self.target_url,
            options={
                "page_timeout": self.page_timeout_value,
                "script_timeout": self.script_timeout_value,
            },
        )

        assert base_fetcher_1.page_timeout == self.page_timeout_value
        assert base_fetcher_1.script_timeout == self.script_timeout_value

        base_fetcher_2 = BaseFetcher(
            config=config,
            url=self.target_url,
            options={
                "script_timeout": self.script_timeout_value,
            },
        )

        assert base_fetcher_2.page_timeout == 30
        assert base_fetcher_2.script_timeout == self.script_timeout_value

        base_fetcher_3 = BaseFetcher(
            config=config,
            url=self.target_url,
            options={
                "page_timeout": self.page_timeout_value,
            },
        )

        assert base_fetcher_3.page_timeout == self.page_timeout_value
        assert base_fetcher_3.script_timeout == 30
