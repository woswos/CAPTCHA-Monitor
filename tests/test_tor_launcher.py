import pytest
import captchamonitor.utils.tor_launcher as tor_launcher
import time


# def test_tor_launcher_start_without_exit_node():
#     tor_config = {'tor_socks_host': '127.0.0.1',
#                   'tor_socks_port': 7070,
#                   'tor_control_port': 7071,
#                   'tor_dir': '/tmp/test_tor_datadir_%s_%s' % (randomString(5), pwd.getpwuid(os.getuid())[0])
#                   }
#     tor_process = tor_launcher.launch_tor_with_config(tor_config)
#     stem_controller = tor_launcher.StemController(tor_config)
#     stem_controller.start()
#
#     time.sleep(3)
#
#     test = (tor_launcher.is_tor_running(tor_config['tor_socks_host'], tor_config['tor_control_port']) == True)
#
#     stem_controller.join()
#     tor_launcher.kill(tor_process)
#
#     assert test == True
