import pytest
import captchamonitor.utils.tor_launcher as tor_launcher
import time


def test_tor_launcher_start_without_exit_node():
    port = 9050
    tor_process = tor_launcher.launch_tor_with_config(port)
    time.sleep(5)
    assert tor_launcher.is_tor_running(port) == True

# def test_tor_launcher_kill_without_exit_node(port):
#     tor_process = test_tor_launcher_start_without_exit_node()
#     tor_launcher.kill(tor_process)
#     time.sleep(5)
#     assert tor_launcher.is_tor_running(port) == False
