import os
import unittest

from captchamonitor.version import __version__
from captchamonitor.utils.config import ENV_VARS, Config
from captchamonitor.utils.exceptions import ConfigInitError


class TestAttrDict(unittest.TestCase):
    def setUp(self):
        self.env_var_default_value = "unittest"

        # Overwrite the current values for testing
        for key, value in ENV_VARS.items():
            os.environ[value] = self.env_var_default_value

    def test_should_init_with_one_dict(self):
        my_dict = Config({"eggs": 42, "spam": "ham"})
        self.assertEqual(my_dict.eggs, 42)
        self.assertEqual(my_dict["eggs"], 42)
        self.assertEqual(my_dict.spam, "ham")
        self.assertEqual(my_dict["spam"], "ham")

    def test_should_not_change_values_by_inited_dict(self):
        base = {"eggs": 42, "spam": "ham"}
        my_dict = Config(base)
        base["eggs"] = 123
        self.assertEqual(my_dict.eggs, 42)
        self.assertEqual(my_dict["eggs"], 42)
        self.assertEqual(my_dict.spam, "ham")
        self.assertEqual(my_dict["spam"], "ham")

    def test_get_item(self):
        my_dict = Config()
        my_dict.test = 123
        self.assertEqual(my_dict.test, 123)
        self.assertEqual(my_dict["test"], 123)

    def test_set_item(self):
        my_dict = Config()
        my_dict["test"] = 123
        self.assertEqual(my_dict["test"], 123)
        self.assertEqual(my_dict.test, 123)

    def test_del_attr(self):
        my_dict = Config()
        my_dict["test"] = 123
        my_dict["python"] = 42
        del my_dict["test"]
        del my_dict.python
        with self.assertRaises(KeyError):
            temp = my_dict["test"]
        with self.assertRaises(AttributeError):
            temp = my_dict.python

    def test_in_should_work_like_in_dict(self):
        my_dict = Config()
        my_dict["test"] = 123
        self.assertIn("test", my_dict)
        self.assertNotIn("bla", my_dict)

    def test_len_should_work_like_in_dict(self):
        my_dict = Config()
        my_dict["test"] = 123
        my_dict.python = 42
        self.assertEqual(len(my_dict), 3 + len(ENV_VARS))

    def test_repr(self):
        my_dict = Config()

        # Create and populate a regular dictionary
        real_dict = {}
        for key, value in ENV_VARS.items():
            real_dict[key] = self.env_var_default_value
        real_dict["version"] = __version__

        self.assertEqual(repr(my_dict), repr(real_dict))

    def test_getting_from_env(self):
        my_dict = Config()
        for key, value in ENV_VARS.items():
            self.assertEqual(my_dict[key], self.env_var_default_value)

    def test_getting_from_env_none_raise_exception(self):
        # Delete the current values for testing
        for key, value in ENV_VARS.items():
            del os.environ[value]

        with self.assertRaises(ConfigInitError):
            my_dict = Config()
