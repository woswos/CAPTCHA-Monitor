# pylint: disable=C0115,C0116,W0212,E1101,W0104

import os

import pytest

from captchamonitor.version import __version__
from captchamonitor.utils.config import ENV_VARS, Config
from captchamonitor.utils.exceptions import ConfigInitError


class TestAttrDict:
    @classmethod
    def setup_class(cls):
        cls.env_var_default_value = "unittest"

        # Overwrite the current values for testing
        for _, value in ENV_VARS.items():
            os.environ[value] = cls.env_var_default_value

    @staticmethod
    def test_should_init_with_one_dict():
        my_dict = Config({"eggs": 42, "spam": "ham"})
        assert my_dict.eggs == 42
        assert my_dict["eggs"] == 42
        assert my_dict.spam == "ham"
        assert my_dict["spam"] == "ham"

    @staticmethod
    def test_should_not_change_values_by_initiated_dict():
        base = {"eggs": 42, "spam": "ham"}
        my_dict = Config(base)
        base["eggs"] = 123
        assert my_dict.eggs == 42
        assert my_dict["eggs"] == 42
        assert my_dict.spam == "ham"
        assert my_dict["spam"] == "ham"

    @staticmethod
    def test_get_item():
        my_dict = Config()
        my_dict.test = 123
        assert my_dict.test == 123
        assert my_dict["test"] == 123

    @staticmethod
    def test_set_item():
        my_dict = Config()
        my_dict["test"] = 123
        assert my_dict["test"] == 123
        assert my_dict.test == 123

    @staticmethod
    def test_del_attr():
        my_dict = Config()
        my_dict["test"] = 123
        my_dict["python"] = 42
        del my_dict["test"]
        del my_dict.python
        with pytest.raises(KeyError):
            my_dict["test"]
        with pytest.raises(AttributeError):
            my_dict.python

    @staticmethod
    def test_in_should_work_like_in_dict():
        my_dict = Config()
        my_dict["test"] = 123
        assert "test" in my_dict
        assert "bla" not in my_dict

    @staticmethod
    def test_len_should_work_like_in_dict():
        my_dict = Config()
        my_dict["test"] = 123
        my_dict.python = 42
        assert len(my_dict) == 3 + len(ENV_VARS)

    @pytest.mark.skip()
    def test_repr(self):
        my_dict = Config()

        # Create and populate a regular dictionary
        real_dict = {}
        for key, _ in ENV_VARS.items():
            real_dict[key] = self.env_var_default_value
        real_dict["version"] = __version__

        assert repr(my_dict) == repr(real_dict)

    @pytest.mark.skip()
    def test_getting_from_env(self):
        my_dict = Config()
        for key, _ in ENV_VARS.items():
            assert my_dict[key] == self.env_var_default_value

    @staticmethod
    def test_getting_from_env_none_raise_exception():
        # Delete the current values for testing
        for _, value in ENV_VARS.items():
            del os.environ[value]

        with pytest.raises(ConfigInitError):
            Config()
