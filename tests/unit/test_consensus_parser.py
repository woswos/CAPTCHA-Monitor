# pylint: disable=C0115,C0116,W0212

from datetime import datetime, timedelta

from captchamonitor.utils.collector import Collector
from captchamonitor.utils.consensus_parser import ConsensusV3Parser, ConsensusRelayEntry


class TestConsensusParser:
    @classmethod
    def setup_class(cls):
        cls.recent_datetime = datetime.now() - timedelta(hours=1)
        cls.consensus_file = Collector().get_consensus(cls.recent_datetime)
        cls.valid_fingerprint = "A53C46F5B157DD83366D45A8E99A244934A14C46"

    def test_consensus_parser_init(self):
        result = ConsensusV3Parser(self.consensus_file)

        assert len(result.relay_entries) > 0
        assert isinstance(result.relay_entries[0], ConsensusRelayEntry)

        # Check if a well know relay is in the list
        found = False
        for relay in result.relay_entries:
            if relay.fingerprint == self.valid_fingerprint:
                found = True
                assert relay.is_exit is True

        assert found is True
