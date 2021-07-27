# pylint: disable=C0115,C0116,W0212,W0238

from captchamonitor.utils.small_scripts import (
    hasattr_private,
    get_random_exit_relay,
    get_random_http_proxy,
)


class TestSmallScripts:
    @staticmethod
    def test_hasattr_private():
        class DummyTestClass:
            def __init__(self):
                self.__private_attribute = "test"

        assert hasattr_private(DummyTestClass(), "__private_attribute") is True
        assert hasattr_private(DummyTestClass(), "__another_attribute") is False

    @staticmethod
    def test_get_random_http_proxy_single(config, tor_proxy):
        single_result = get_random_http_proxy(config=config, tor_proxy=tor_proxy)
        assert isinstance(single_result, tuple)
        assert isinstance(single_result[0], str)
        assert isinstance(single_result[1], int)

    @staticmethod
    def test_get_random_http_proxy_multiple(config, tor_proxy):
        multiple_result = get_random_http_proxy(
            config=config, tor_proxy=tor_proxy, multiple=True
        )
        assert len(multiple_result) >= 1
        assert isinstance(multiple_result, list)
        assert isinstance(multiple_result[0], tuple)
        assert isinstance(multiple_result[0][0], str)
        assert isinstance(multiple_result[0][1], int)

    @staticmethod
    def test_get_random_exit_relay():
        single_result = get_random_exit_relay()
        assert isinstance(single_result, str)

        multiple_result = get_random_exit_relay(multiple=True)
        assert isinstance(multiple_result, list)
        assert isinstance(multiple_result[0], str)
