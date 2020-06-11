import pytest
import captchamonitor.utils.tor_launcher as tor_launcher
import time


def test_tor_launcher_start_without_exit_node():
    socks_host = '127.0.0.1'
    socks_port = 9050
    control_port = 9051
    tor_process = tor_launcher.launch_tor_with_config(socks_host, socks_port, control_port)
    time.sleep(3)
    test = (tor_launcher.is_tor_running(socks_host, control_port) == True)
    tor_launcher.kill(tor_process)
    assert test == True

# def test_tor_launcher_kill_without_exit_node(port):
#     tor_process = test_tor_launcher_start_without_exit_node()
#     tor_launcher.kill(tor_process)
#     time.sleep(5)
#     assert tor_launcher.is_tor_running(port) == False
