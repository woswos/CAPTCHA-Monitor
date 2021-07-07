# pylint: disable=C0115,C0116,W0212

import pytest

from captchamonitor.utils.exceptions import TorLauncherInitError
from captchamonitor.utils.tor_launcher import TorLauncher
from captchamonitor.utils.small_scripts import deep_copy


class TestTorLauncher:
    @staticmethod
    def test_tor_launcher_init(config):
        TorLauncher(config)

    @staticmethod
    def test_wrong_network_name(config):
        test_config = deep_copy(config)

        # Modify the network name
        test_config["docker_network"] = "obviously_wrong_network"

        # Try intializing
        with pytest.raises(TorLauncherInitError):
            TorLauncher(test_config)
