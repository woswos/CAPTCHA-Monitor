from datetime import datetime

from freezegun import freeze_time

from captchamonitor.utils.models import Relay, MetaData
from captchamonitor.utils.onionoo import Onionoo
from captchamonitor.core.update_relays import UpdateRelays
from captchamonitor.utils.consensus_parser import ConsensusRelayEntry


class TestUpdateRelays:
    @classmethod
    def setup_class(cls):
        cls.csailmitexit_fpr = "A53C46F5B157DD83366D45A8E99A244934A14C46"
        cls.consensus_relay_entry = ConsensusRelayEntry(
            nickname="csailmitexit",
            identity="B2GX5y1BRdre5CumPWY/sdc6RPs",
            digest="test",
            publication=datetime.now(),
            IP="127.0.0.1",
            IPv6="4ffa:49b3:6b32:0bd7:c8af:45ee:5c22:16c5",
            IPv6ORPort="0",
            is_exit=True,
            ORPort=0,
            DirPort=0,
            bandwidth=0,
            flags=["test"],
        )

    def test_update_relays_init(self, config, db_session):
        db_metadata_query = db_session.query(MetaData)

        # Make sure there is not metadata present in db
        assert db_metadata_query.count() == 0

        update_relays = UpdateRelays(
            config=config, db_session=db_session, auto_update=False
        )

        assert update_relays._UpdateRelays__hours_since_last_update() == 1

        # Call again in the simulated future
        with freeze_time("2100-01-01"):
            assert update_relays._UpdateRelays__hours_since_last_update() > 100

    def test__insert_batch_into_db(self, config, db_session):
        db_relay_query = db_session.query(Relay)

        update_relays = UpdateRelays(
            config=config, db_session=db_session, auto_update=False
        )

        # Get Onionoo data
        onionoo_relay_data = Onionoo([self.csailmitexit_fpr]).relay_entries

        # Parse the consensus file
        parsed_consensus = {self.csailmitexit_fpr: self.consensus_relay_entry}

        # Check if the relay table is empty
        assert db_relay_query.count() == 0

        update_relays._UpdateRelays__insert_batch_into_db(
            onionoo_relay_data, parsed_consensus
        )

        # Check if the relay table was populated with correct data
        assert db_relay_query.count() == 1
        assert db_relay_query.first().fingerprint == self.csailmitexit_fpr

    def test_update_relays_init_with_already_populated_table(self, config, db_session):
        db_relay_query = db_session.query(Relay)

        # Prepopulate the table
        update_relays = UpdateRelays(
            config=config, db_session=db_session, auto_update=False
        )
        onionoo_relay_data = Onionoo([self.csailmitexit_fpr]).relay_entries
        parsed_consensus = {self.csailmitexit_fpr: self.consensus_relay_entry}

        assert db_relay_query.count() == 0

        update_relays._UpdateRelays__insert_batch_into_db(
            onionoo_relay_data, parsed_consensus
        )

        assert db_relay_query.count() == 1
        assert db_relay_query.first().fingerprint == self.csailmitexit_fpr

        # Try inserting the same relay again with different details
        update_relays._UpdateRelays__insert_batch_into_db(
            onionoo_relay_data, parsed_consensus
        )

        # Make sure there still only one relay
        assert db_relay_query.count() == 1
        assert db_relay_query.first().fingerprint == self.csailmitexit_fpr
