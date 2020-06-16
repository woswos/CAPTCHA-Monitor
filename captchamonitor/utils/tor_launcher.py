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


class TorLauncher():
    def __init__(self):
        # Take what you need out of the config dictionary
        self.socks_host = os.environ['CM_TOR_HOST']
        self.socks_port = os.environ['CM_TOR_SOCKS_PORT']
        self.control_port = int(os.environ['CM_TOR_CONTROL_PORT'])
        self.tor_dir = os.environ['CM_TOR_DIR_PATH']

    def start(self):
        self.tor_process = self.launch_tor_process()
        self.stem_controller = StemController(self.socks_host, self.control_port, self.tor_dir)
        self.stem_controller.start()
        self.last_circuit_was_successful = False

    def print_bootstrap_lines(self, line):
        if "Bootstrapped " in line:
            logger.debug(line)

    def launch_tor_process(self):
        """
        Only launches the Tor process but does not create any circuits
        """
        config = {
            'SocksPort': '%s:%s' % (str(self.socks_host), str(self.socks_port)),
            'ControlPort': '%s:%s' % (str(self.socks_host), str(self.control_port)),
            'DataDirectory': self.tor_dir,
            'CookieAuthentication': '1',
            'PathsNeededToBuildCircuits': '0.95',
            'LearnCircuitBuildTimeout': '0',
            'CircuitBuildTimeout': '10',
            '__DisablePredictedCircuits': '1',
            '__LeaveStreamsUnattached': '1',
            'FetchHidServDescriptors': '0',
            'MaxCircuitDirtiness': '10',
            'UseMicroDescriptors': '0'
            # 'FetchServerDescriptors': '0'
        }

        try:
            tor_process = stem.process.launch_tor_with_config(
                config=config,
                timeout=300,
                init_msg_handler=self.print_bootstrap_lines,
                completion_percent=75,
                take_ownership=True)
            logger.info('Launched Tor at port %s:%s' % (self.socks_host, self.socks_port))

        except Exception as err:
            logger.error('stem.process.launch_tor_with_config() says: %s' % err)
            return False

        return tor_process

    def new_circuit(self, exit_node_ip=None):
        """
        Just a wrapper for StemController's new_circuit()
        """
        return self.stem_controller.new_circuit(exit_node_ip)

    def get_exit_relays(self):
        # """
        # Just a wrapper for StemController's get_exit_relays()
        # """
        # return self.stem_controller.get_exit_relays()

        relays = {}
        # Get relay descriptors from the cached location
        for desc in parse_file(os.path.join(self.tor_dir, 'cached-consensus')):
            if desc.exit_policy.is_exiting_allowed():
                relays[desc.address] = desc.fingerprint

        return relays

    def stop(self):
        # Gracefully stop the stem controller thread
        logger.debug('Stopping the stem controller')
        self.stem_controller.join()

        try:
            logger.debug('Killing the Tor process')
            self.tor_process.kill()
        except Exception as err:
            logger.error('tor_process.kill() says: %s' % err)
        return True


class StemController(threading.Thread):
    """
    StemController class that runs in a seperate thread. So that it can handle
        the incoming stream and connect them to created circuits.
    """

    def __init__(self, tor_socks_host, tor_control_port, tor_dir):
        """
        constructor, setting initial variables
        """
        self._stop_event = threading.Event()
        self._sleep_period = 0.01
        threading.Thread.__init__(self, name='StemController')

        # Take what you need out of the config dictionary
        self.tor_socks_host = tor_socks_host
        self.tor_control_port = tor_control_port
        self.tor_dir = tor_dir

        # Connect stem controller to the Tor process
        self.controller = Controller.from_port(
            address=self.tor_socks_host, port=int(self.tor_control_port))
        self.controller.authenticate()

        # No need to download descriptors anymore
        self.controller.set_conf("FetchServerDescriptors", "0")

        self.circ_id = None

    def run(self):
        """
        Main loop
        """
        # Add the listener for handling streams for us
        self.controller.add_event_listener(
            self.attach_stream, stem.control.EventType.STREAM)

        # Just keep looping to keep the thread alive
        while not self._stop_event.isSet():
            # Wait a little bit until running the next loop
            self._stop_event.wait(self._sleep_period)

        self.controller.remove_event_listener(self.attach_stream)

        # Close open circuits before killing the thread
        logger.debug('Closing the circuits')
        for circuit in self.controller.get_circuits():
            self.controller.close_circuit(circuit.id)
            logger.debug('Closed circuit %s' % str(circuit.id))

        self.controller.close()

    def attach_stream(self, stream):
        """
        Attaches given stream to the custom created circuit
        """
        # see https://stem.torproject.org/tutorials/to_russia_with_love.html#custom-path-selection
        # Wait until the user creates a circuit
        if self.circ_id:
            if(stream.status == 'NEW'):
                logger.debug('Attaching stream (%s) to circuit %s' %
                             (stream.target_address, self.circ_id))

                try:
                    self.controller.attach_stream(stream.id, self.circ_id)
                except Exception as err:
                    logger.debug('Could not attach stream: %s', err)

    def join(self, timeout=None):
        """
        Stop the thread and wait for it to end
        """
        try:
            self._stop_event.set()
            threading.Thread.join(self, timeout)

        except Exception as err:
            logger.error('stem_controller() says: %s' % err)

    def get_exit_relays(self):
        """
        Gets all exit relays from the cached Tor directory and returns a dictionary
            of relay fingerprints and IP addresses
        """
        relays = {}

        # to do: do not download descriptors every single time
        # for desc in stem.descriptor.remote.get_server_descriptors():
        #     if desc.exit_policy.is_exiting_allowed():
        #         relays[desc.address] = desc.fingerprint

        # Get relay descriptors from the cached location
        for desc in parse_file(os.path.join(self.tor_dir, 'cached-consensus')):
            if desc.exit_policy.is_exiting_allowed():
                relays[desc.address] = desc.fingerprint

        return relays

    def new_circuit(self, exit_node_ip=None):
        """
        Creates a new circuit using the given exit node. If a node exit was not
            provided, it chooses one randomly. Returns the circuit id.
        """
        relays = self.get_exit_relays()

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

        try:
            # Close the previous circuit
            if self.circ_id and self.last_circuit_was_successful:
                self.controller.close_circuit(self.circ_id)
        except Exception as err:
            logger.debug('Could not close the previous circuit: %s', err)

        try:
            # Establish the new circuit
            self.circ_id = self.controller.new_circuit(path=path, await_build=True)
            self.last_circuit_was_successful = True
        except Exception as err:
            self.last_circuit_was_successful = False
            logger.debug('Could not create the requested circuit: %s', err)
            return False

        return True
