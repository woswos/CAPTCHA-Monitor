# pylint: disable=C0115,C0116,W0212

import os

import pytest

from captchamonitor.cm import CaptchaMonitor
from captchamonitor.utils.config import ENV_VARS


class TestCaptchaMonitor:
    @staticmethod
    def test_captcha_monitor_failed_init():
        # Delete the current values for testing
        for _, value in ENV_VARS.items():
            if value in os.environ:
                del os.environ[value]

        # Try to initialize
        with pytest.raises(SystemExit):
            CaptchaMonitor()
