import unittest
from datetime import datetime, timedelta

import pytest

from captchamonitor.utils.collector import Collector
from captchamonitor.utils.consensus_parser import ConsensusV3Parser, ConsensusRelayEntry


class TestConsensusParser(unittest.TestCase):
    def setUp(self):
        self.recent_datetime = datetime.now() - timedelta(hours=1)
        self.consensus_file = Collector().get_consensus(self.recent_datetime)
        self.valid_fingerprint = "A53C46F5B157DD83366D45A8E99A244934A14C46"

    def test_consensus_parser_init(self):
        result = ConsensusV3Parser(self.consensus_file)

        self.assertGreater(len(result.relay_entries), 0)
        self.assertEqual(type(result.relay_entries[0]), ConsensusRelayEntry)

        # Check if a well know relay is in the list
        found = False
        for relay in result.relay_entries:
            if relay.fingerprint == self.valid_fingerprint:
                found = True
                self.assertTrue(relay.is_exit)

        self.assertTrue(found)
