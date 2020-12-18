#!/usr/bin/env python3

"""
Launch Tor with given configuration values
"""

import logging
import os
import random
import threading
from pathlib import Path

import stem.descriptor.remote
import stem.process
from stem.control import Controller
from stem.descriptor import parse_file


class TorLauncher:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

        try:
            # Take what you need out of the config dictionary
            self.socks_host = os.environ["CM_TOR_HOST"]
            self.socks_port = os.environ["CM_TOR_SOCKS_PORT"]
            self.control_port = int(os.environ["CM_TOR_CONTROL_PORT"])
            self.tor_dir = os.environ["CM_TOR_DIR_PATH"]
        except Exception as err:
            self.logger.error(
                "Some of the environment variables are missing: %s", err
            )

    def start(self):
        self.tor_process = self.launch_tor_process()
        self.bind_controller(self.socks_host, self.control_port, self.tor_dir)

    def bind_controller(self, socks_host, control_port, tor_dir):
        self.stem_controller = StemController(socks_host, control_port, tor_dir)
        self.stem_controller.start()
        self.last_circuit_was_successful = False

    def print_bootstrap_lines(self, line):
        if "Bootstrapped " in line:
            self.logger.debug(line)

    def launch_tor_process(self):
        """
        Only launches the Tor process but does not create any circuits
        """
        config = {
            "SocksPort": "%s:%s" % (str(self.socks_host), str(self.socks_port)),
            "ControlPort": "%s:%s"
            % (str(self.socks_host), str(self.control_port)),
            "DataDirectory": self.tor_dir,
            "CookieAuthentication": "1",
            "PathsNeededToBuildCircuits": "0.95",
            "LearnCircuitBuildTimeout": "0",
            "CircuitBuildTimeout": "10",
            "__DisablePredictedCircuits": "1",
            "__LeaveStreamsUnattached": "1",
            "FetchHidServDescriptors": "0",
            "MaxCircuitDirtiness": "10",
            "UseMicroDescriptors": "1",
        }

        try:
            tor_process = stem.process.launch_tor_with_config(
                config=config,
                timeout=300,
                init_msg_handler=self.print_bootstrap_lines,
                completion_percent=75,
                take_ownership=True,
            )
            self.logger.debug(
                "Launched Tor at port %s:%s"
                % (self.socks_host, self.socks_port)
            )

        except Exception as err:
            self.logger.error(
                "stem.process.launch_tor_with_config() says: %s" % err
            )
            return False

        return tor_process

    def new_circuit(self, exit_node_ip=None, timeout=10):
        """
        Just a wrapper for StemController's new_circuit()
        """
        return self.stem_controller.new_circuit(exit_node_ip, timeout)

    def get_exit_relays(self):
        relays = {}
        # Get relay descriptors from the cached location
        for desc in parse_file(os.path.join(self.tor_dir, "cached-consensus")):
            if desc.exit_policy.is_exiting_allowed():
                relays[desc.address] = desc.fingerprint

        return relays

    def get_consensus(self, use_local_dir=False):

        relays = []
        relays_with_ipv6_exit_policy = []

        # Get the list of relays that allow IPv6 exiting
        if use_local_dir:
            descriptors_dest = parse_file(
                os.path.join(str(Path.home()), ".tor", "cached-descriptors")
            )
        else:
            descriptors_dest = stem.descriptor.remote.get_server_descriptors()

        for desc in descriptors_dest:
            if desc.exit_policy_v6.is_exiting_allowed():
                relays_with_ipv6_exit_policy.append(desc.fingerprint)

        # Get the most recent consensus
        if use_local_dir:
            consensus_dest = parse_file(
                os.path.join(str(Path.home()), ".tor", "cached-consensus")
            )
        else:
            consensus_dest = stem.descriptor.remote.get_consensus()

        for desc in consensus_dest:
            relay = {
                "nickname": desc.nickname,
                "fingerprint": desc.fingerprint,
                "address": desc.address,
                "is_ipv4_exiting_allowed": str(
                    int(desc.exit_policy.is_exiting_allowed())
                ),
                "is_ipv6_exiting_allowed": str(
                    int(desc.fingerprint in relays_with_ipv6_exit_policy)
                ),
                "published": desc.published,
            }

            relays.append(relay)

        return relays

    def stop(self):
        # Gracefully stop the stem controller thread
        self.logger.debug("Stopping the stem controller")
        self.stem_controller.join()

        try:
            self.logger.debug("Killing the Tor process")
            self.tor_process.kill()
        except Exception as err:
            self.logger.error("tor_process.kill() says: %s" % err)
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
        self.logger = logging.getLogger(__name__ + "_stem_controller")
        self._stop_event = threading.Event()
        self._sleep_period = 0.01
        threading.Thread.__init__(self, name="StemController")

        # Take what you need out of the config dictionary
        self.tor_socks_host = tor_socks_host
        self.tor_control_port = tor_control_port
        self.tor_dir = tor_dir

        # Connect stem controller to the Tor process
        self.controller = Controller.from_port(
            address=self.tor_socks_host, port=int(self.tor_control_port)
        )
        self.controller.authenticate()

        # <strike> No need to download descriptors anymore </strike>
        # Not downloading the descriptors causes problems in the long run
        #   and this software is intended to be running continously. So,
        #   we should not disable this.
        # self.controller.set_conf("FetchServerDescriptors", "0")

        self.circ_id = None

    def run(self):
        """
        Main loop
        """
        # Add the listener for handling streams for us
        self.controller.add_event_listener(
            self.attach_stream, stem.control.EventType.STREAM
        )

        # Just keep looping to keep the thread alive
        while not self._stop_event.isSet():
            # Wait a little bit until running the next loop
            self._stop_event.wait(self._sleep_period)

        self.controller.remove_event_listener(self.attach_stream)

        # Close open circuits before killing the thread
        self.logger.debug("Closing the circuits")
        for circuit in self.controller.get_circuits():
            self.controller.close_circuit(circuit.id)
            self.logger.debug("Closed circuit %s" % str(circuit.id))

        self.controller.close()

    def attach_stream(self, stream):
        """
        Attaches given stream to the custom created circuit
        """
        # see https://stem.torproject.org/tutorials/to_russia_with_love.html#custom-path-selection
        # Wait until the user creates a circuit
        if self.circ_id:
            if stream.status == "NEW":
                for i in range(3):
                    try:
                        if ".onion" in str(stream.target_address):
                            self.logger.debug(
                                "Attaching onion services is not supported currently"
                            )
                            # self.controller.attach_stream(stream.id, '0')
                        else:
                            self.logger.debug(
                                "Attaching stream (%s) to circuit %s"
                                % (stream.target_address, self.circ_id)
                            )
                            self.controller.attach_stream(
                                stream.id, self.circ_id
                            )
                        break
                    except Exception as err:
                        # if str(err).startswith('Unknown circuit '):
                        #     self.logger.debug('Trying to recreate circuit %s' % self.circ_id)
                        #     self.refresh_circuit()
                        # else:
                        #     self.logger.debug('Could not attach stream: %s', err)
                        #     break
                        self.logger.debug("Could not attach stream: %s", err)

    def join(self, timeout=None):
        """
        Stop the thread and wait for it to end
        """
        try:
            self._stop_event.set()
            threading.Thread.join(self, timeout)

        except Exception as err:
            self.logger.error("stem_controller() says: %s" % err)

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

        # # Get relay descriptors from the cached location
        # for desc in parse_file(os.path.join(self.tor_dir, 'cached-microdesc-consensus')):
        #     if desc.exit_policy.is_exiting_allowed():
        #         relays[desc.address] = desc.fingerprint
        #
        # return relays

        exit_digests = []
        data_dir = self.controller.get_conf("DataDirectory")

        for desc in self.controller.get_microdescriptors():
            if desc.exit_policy.is_exiting_allowed():
                exit_digests.append(
                    desc.digest(hash_type="SHA256", encoding="BASE64")
                )

        for desc in parse_file(
            os.path.join(data_dir, "cached-microdesc-consensus")
        ):
            if desc.microdescriptor_digest in exit_digests:
                relays[desc.address] = desc.fingerprint

        return relays

    def refresh_circuit(self):
        self.new_circuit(self.exit_node_ip)

    def new_circuit(self, exit_node_ip=None, timeout=10):
        """
        Creates a new circuit using the given exit node. If a node exit was not
            provided, it chooses one randomly. Returns the exit node ip.
        """
        self.exit_node_ip = exit_node_ip

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
            self.logger.debug("Could not close the previous circuit: %s", err)

        try:
            # Establish the new circuit
            self.circ_id = self.controller.new_circuit(
                path=path, await_build=True, timeout=timeout
            )
            self.last_circuit_was_successful = True
            self.logger.debug("Created the requested circuit %s" % self.circ_id)
        except Exception as err:
            self.last_circuit_was_successful = False
            self.logger.debug("Could not create the requested circuit: %s", err)

        return exit_node_ip
