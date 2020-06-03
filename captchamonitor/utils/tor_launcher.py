#!/usr/bin/env python3

"""
Launch Tor with given configuration values
"""

import stem.process
import logging
from selenium.webdriver.common.utils import is_connectable

logger = logging.getLogger(__name__)


def print_bootstrap_lines(line):
    if "Bootstrapped " in line:
        logger.debug(line)


def launch_tor_with_config(port, exit_node=None):
    if exit_node is None:
        config = {
            'SocksPort': str(port)
        }
    else:
        config = {
            'SocksPort': str(port),
            'ExitNodes': str(exit_node),
        }

    try:
        tor_process = stem.process.launch_tor_with_config(
            config=config, init_msg_handler=print_bootstrap_lines)
        logger.debug('Launched Tor at port %s' % port)

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


def is_tor_running(port):
    if not is_connectable(port):
        #logger.critical('Is Tor running at port %s? I can\'t detect it', tor_socks_port)
        return False

    return True
