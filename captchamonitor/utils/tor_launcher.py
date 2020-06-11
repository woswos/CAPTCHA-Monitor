#!/usr/bin/env python3

"""
Launch Tor with given configuration values
"""

import stem.process
from stem.control import Controller
import logging
import pwd
import os

logger = logging.getLogger(__name__)


def print_bootstrap_lines(line):
    if "Bootstrapped " in line:
        logger.debug(line)


def launch_tor_with_config(socks_host, socks_port, control_port, exit_node=None):
    tor_dir = "/tmp/captchamonitor_tor_datadir_" + pwd.getpwuid(os.getuid())[0]

    config = {
        'SocksPort': '%s:%s' % (str(socks_host), str(socks_port)),
        'ControlPort': '%s:%s' % (str(socks_host), str(control_port)),
        'DataDirectory': tor_dir,
        'CookieAuthentication': '1',
        'PathsNeededToBuildCircuits': '0.95',
        'LearnCircuitBuildTimeout': '0',
        'CircuitBuildTimeout': '40',
        #'__DisablePredictedCircuits': '1',
        #'__LeaveStreamsUnattached': '1',
        'FetchHidServDescriptors': '0',
        'UseMicroDescriptors': '0'
    }

    if exit_node is not None:
        config['ExitNodes'] = str(exit_node)

    try:
        tor_process = stem.process.launch_tor_with_config(
            config=config,
            timeout=300,
            init_msg_handler=print_bootstrap_lines,
            take_ownership=True)
        logger.debug('Launched Tor at port %s:%s' % (socks_host, socks_port))

    except Exception as err:
        logger.error('stem.process.launch_tor_with_config() says: %s' % err)
        return False

    return tor_process


def kill(tor_process):
    try:
        tor_process.kill()
    except Exception as err:
        logger.error('tor_process.kill() says: %s' % err)
    return True


def is_tor_running(socks_host, control_port):
    try:
        with Controller.from_port(address=socks_host, port=control_port) as controller:
            controller.authenticate()

    except Exception as err:
        logger.error('Controller.from_port() says: %s' % err)
        print('Controller.from_port() says: %s' % err)
        return False

    return True
