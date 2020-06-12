#!/usr/bin/env python3

"""
Launch Tor with given configuration values
"""

import stem.process
from stem.control import Controller
from stem.descriptor import parse_file
import stem.descriptor.remote
import logging
import os
import threading
import random

logger = logging.getLogger(__name__)


def print_bootstrap_lines(line):
    if "Bootstrapped " in line:
        logger.debug(line)


def launch_tor_with_config(tor_config):
    socks_host = tor_config['tor_socks_host']
    socks_port = tor_config['tor_socks_port']
    control_port = tor_config['tor_control_port']
    exit_node = tor_config['exit_node']
    tor_dir = tor_config['tor_dir']

    config = {
        'SocksPort': '%s:%s' % (str(socks_host), str(socks_port)),
        'ControlPort': '%s:%s' % (str(socks_host), str(control_port)),
        'DataDirectory': tor_dir,
        'CookieAuthentication': '1',
        'PathsNeededToBuildCircuits': '0.95',
        'LearnCircuitBuildTimeout': '0',
        'CircuitBuildTimeout': '40',
        '__DisablePredictedCircuits': '1',
        '__LeaveStreamsUnattached': '1',
        'FetchHidServDescriptors': '0',
        'UseMicroDescriptors': '0'
        # 'FetchServerDescriptors': '0'
    }

    if exit_node is not None:
        config['ExitNodes'] = str(exit_node)

    try:
        tor_process = stem.process.launch_tor_with_config(
            config=config,
            timeout=300,
            init_msg_handler=print_bootstrap_lines,
            completion_percent=75,
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
        return False

    return True


class StemController(threading.Thread):
    """
    StemController class that runs in a seperate thread. So that it can handle
        the incoming stream and connect them to created circuits.
    """
    def __init__(self, tor_config):
        """
        constructor, setting initial variables
        """
        self._stop_event = threading.Event()
        self._sleep_period = 0.5
        threading.Thread.__init__(self, name='StemController')
        self.tor_socks_host = tor_config['tor_socks_host']
        self.tor_control_port = tor_config['tor_control_port']
        self.exit_node = tor_config['exit_node']
        self.tor_socks_port = tor_config['tor_socks_port']
        self.tor_dir = tor_config['tor_dir']

    def run(self):
        """
        main loop
        """
        exit_node_ip = self.exit_node
        tor_dir = self.tor_dir
        relays = {}

        # to do: do not download descriptors every single time
        # for desc in stem.descriptor.remote.get_server_descriptors():
        #     if desc.exit_policy.is_exiting_allowed():
        #         relays[desc.address] = desc.fingerprint

        # Get relay descriptors from the cached location
        for desc in parse_file(os.path.join(tor_dir, 'cached-consensus')):
            if desc.exit_policy.is_exiting_allowed():
                relays[desc.address] = desc.fingerprint

        # If no exit node was specified
        if exit_node_ip is None:
            exit_node_ip = random.choice(list(relays.keys()))

        # Choose a first hop that is not same as the exit node
        while True:
            first_hop_ip = random.choice(list(relays.keys()))
            if first_hop_ip is not exit_node_ip:
                break

        first_hop_fpr = relays[first_hop_ip]
        exit_node_fpr = relays[exit_node_ip]

        path = [first_hop_fpr, exit_node_fpr]

        with Controller.from_port(address=self.tor_socks_host, port=int(self.tor_control_port)) as controller:
            controller.authenticate()

            # No need to download descriptors anymore
            controller.set_conf("FetchServerDescriptors", "0")

            # Establish the circuit using the path
            try:
                circ_id = controller.new_circuit(path=path, await_build=True)
            except Exception as err:
                logger.debug('Could not establish the circuit: %s', err)

            # Keep looping to connect new streams to the circuit
            while not self._stop_event.isSet():
                for i in controller.get_streams():
                    if((i.status != 'SUCCEEDED')):
                        logger.debug('Attaching stream (%s) to circuit %s' %
                                     (i.target_address, circ_id))

                        try:
                            controller.attach_stream(i.id, circ_id)
                        except Exception as err:
                            logger.debug('Could not attach stream: %s', err)

                # Wait a little bit until running the next loop
                self._stop_event.wait(self._sleep_period)

            # Close the circuit once we are done
            controller.close_circuit(circ_id)

    def join(self, timeout=None):
        """
        stop the thread and wait for it to end
        """
        self._stop_event.set()
        threading.Thread.join(self, timeout)
