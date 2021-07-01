from captchamonitor.utils.small_scripts import *


class TestSmallScripts:
    def test_hasattr_private(self):
        class DummyTestClass:
            def __init__(self):
                self.__private_attribute = "test"

        assert hasattr_private(DummyTestClass(), "__private_attribute") == True
        assert hasattr_private(DummyTestClass(), "__another_attribute") == False
