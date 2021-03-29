import os
import unittest
from captchamonitor.utils.config import Config, ENV_VARS
from captchamonitor.utils.exceptions import ConfigInitError


class TestAttrDict(unittest.TestCase):
    def setUp(self):
        self.env_var_default_value = "unittest"

        # Overwrite the current values for testing
        for key, value in ENV_VARS.items():
            os.environ[value] = self.env_var_default_value

    def test_should_init_with_one_dict(self):
        my_dict = Config({"eggs": 42, "spam": "ham"})
        self.assertEquals(my_dict.eggs, 42)
        self.assertEquals(my_dict["eggs"], 42)
        self.assertEquals(my_dict.spam, "ham")
        self.assertEquals(my_dict["spam"], "ham")

    def test_should_not_change_values_by_inited_dict(self):
        base = {"eggs": 42, "spam": "ham"}
        my_dict = Config(base)
        base["eggs"] = 123
        self.assertEquals(my_dict.eggs, 42)
        self.assertEquals(my_dict["eggs"], 42)
        self.assertEquals(my_dict.spam, "ham")
        self.assertEquals(my_dict["spam"], "ham")

    def test_get_item(self):
        my_dict = Config()
        my_dict.test = 123
        self.assertEquals(my_dict.test, 123)
        self.assertEquals(my_dict["test"], 123)

    def test_set_item(self):
        my_dict = Config()
        my_dict["test"] = 123
        self.assertEquals(my_dict["test"], 123)
        self.assertEquals(my_dict.test, 123)

    def test_del_attr(self):
        my_dict = Config()
        my_dict["test"] = 123
        my_dict["python"] = 42
        del my_dict["test"]
        del my_dict.python
        with self.assertRaises(ConfigInitError):
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
        self.assertEquals(len(my_dict), 2 + len(ENV_VARS))

    def test_getting_from_env(self):
        my_dict = Config()
        for key, value in ENV_VARS.items():
            self.assertEquals(my_dict[key], self.env_var_default_value)
