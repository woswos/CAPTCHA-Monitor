import os
import pytest
import unittest
from captchamonitor.utils.config import ENV_VARS
from captchamonitor.cm import CaptchaMonitor


class TestAttrDict(unittest.TestCase):
    def setUp(self):
        pass

    def test_captcha_monitor_failed_init(self):
        # Delete the current values for testing
        for key, value in ENV_VARS.items():
            if value in os.environ:
                del os.environ[value]

        # Try to initialize
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            CaptchaMonitor()

        # Check if code exits
        self.assertEqual(pytest_wrapped_e.type, SystemExit)
