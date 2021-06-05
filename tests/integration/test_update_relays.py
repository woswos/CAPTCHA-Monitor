import unittest
from datetime import datetime

import pytest
from freezegun import freeze_time

from captchamonitor.utils.config import Config
from captchamonitor.utils.models import Relay, MetaData
from captchamonitor.utils.onionoo import Onionoo
from captchamonitor.utils.database import Database
from captchamonitor.core.update_relays import UpdateRelays
from captchamonitor.utils.consensus_parser import ConsensusRelayEntry


class TestUpdateRelays(unittest.TestCase):
    def setUp(self):
        self.config = Config()
        self.database = Database(
            self.config["db_host"],
            self.config["db_port"],
            self.config["db_name"],
            self.config["db_user"],
            self.config["db_password"],
        )
        self.db_session = self.database.session()
        self.db_metadata_query = self.db_session.query(MetaData)
        self.db_relay_query = self.db_session.query(Relay)
        self.csailmitexit_fpr = "A53C46F5B157DD83366D45A8E99A244934A14C46"
        self.consensus_relay_entry = ConsensusRelayEntry(
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

    def tearDown(self):
        self.db_session.close()

    def test_update_relays_init(self):
        # Make sure there is not metadata present in db
        self.assertEqual(self.db_metadata_query.count(), 0)

        update_relays = UpdateRelays(
            config=self.config, db_session=self.db_session, auto_update=False
        )

        self.assertEqual(update_relays._UpdateRelays__hours_since_last_update(), 0)

        # Call again in the simulated future
        with freeze_time("2100-01-01"):
            self.assertGreater(
                update_relays._UpdateRelays__hours_since_last_update(), 100
            )

    def test__insert_batch_into_db(self):
        update_relays = UpdateRelays(
            config=self.config, db_session=self.db_session, auto_update=False
        )

        # Get Onionoo data
        onionoo_relay_data = Onionoo([self.csailmitexit_fpr]).relay_entries

        # Parse the consensus file
        parsed_consensus = {self.csailmitexit_fpr: self.consensus_relay_entry}

        # Check if the relay table is empty
        self.assertEqual(self.db_relay_query.count(), 0)

        update_relays._UpdateRelays__insert_batch_into_db(
            onionoo_relay_data, parsed_consensus
        )

        # Check if the relay table was populated with correct data
        self.assertEqual(self.db_relay_query.count(), 1)
        self.assertEqual(self.db_relay_query.first().fingerprint, self.csailmitexit_fpr)

    def test_update_relays_init_with_already_populated_table(self):
        # Prepopulate the table
        update_relays = UpdateRelays(
            config=self.config, db_session=self.db_session, auto_update=False
        )
        onionoo_relay_data = Onionoo([self.csailmitexit_fpr]).relay_entries
        parsed_consensus = {self.csailmitexit_fpr: self.consensus_relay_entry}
        self.assertEqual(self.db_relay_query.count(), 0)
        update_relays._UpdateRelays__insert_batch_into_db(
            onionoo_relay_data, parsed_consensus
        )
        self.assertEqual(self.db_relay_query.count(), 1)
        self.assertEqual(self.db_relay_query.first().fingerprint, self.csailmitexit_fpr)

        # Try inserting the same relay again with different details
        update_relays._UpdateRelays__insert_batch_into_db(
            onionoo_relay_data, parsed_consensus
        )

        # Make sure there still only one relay
        self.assertEqual(self.db_relay_query.count(), 1)
        self.assertEqual(self.db_relay_query.first().fingerprint, self.csailmitexit_fpr)
