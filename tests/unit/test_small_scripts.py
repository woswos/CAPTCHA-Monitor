# pylint: disable=C0115,C0116,W0212,W0238

from captchamonitor.utils.small_scripts import hasattr_private


class TestSmallScripts:
    @staticmethod
    def test_hasattr_private():
        class DummyTestClass:
            def __init__(self):
                self.__private_attribute = "test"

        assert hasattr_private(DummyTestClass(), "__private_attribute") is True
        assert hasattr_private(DummyTestClass(), "__another_attribute") is False
