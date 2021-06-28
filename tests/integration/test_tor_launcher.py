import pytest

from captchamonitor.utils.exceptions import TorLauncherInitError
from captchamonitor.utils.tor_launcher import TorLauncher
from captchamonitor.utils.small_scripts import deep_copy


class TestTorLauncher:
    def test_tor_launcher_init(self, config):
        TorLauncher(config)

    def test_wrong_network_name(self, config):
        test_config = deep_copy(config)

        # Modify the network name
        test_config["docker_network"] = "obviously_wrong_network"

        # Try intializing
        with pytest.raises(TorLauncherInitError):
            TorLauncher(test_config)
