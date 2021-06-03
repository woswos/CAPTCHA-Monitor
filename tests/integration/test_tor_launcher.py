import unittest

import pytest

from captchamonitor.utils.config import Config
from captchamonitor.utils.exceptions import TorLauncherInitError
from captchamonitor.utils.tor_launcher import TorLauncher
from captchamonitor.utils.small_scripts import deep_copy


class TestTorLauncher(unittest.TestCase):
    def setUp(self):
        self.config = Config()

    def test_tor_launcher_init(self):
        TorLauncher(self.config)

    def test_wrong_network_name(self):
        test_config = deep_copy(self.config)

        # Modify the network name
        test_config["docker_network"] = "obviously_wrong_network"

        # Try intializing
        with pytest.raises(TorLauncherInitError) as pytest_wrapped_e:
            TorLauncher(test_config)

        # Check if the exception is correct
        self.assertEqual(pytest_wrapped_e.type, TorLauncherInitError)
