import logging
from typing import Dict, List
from datetime import datetime

from sqlalchemy.orm import sessionmaker

from captchamonitor.utils.config import Config
from captchamonitor.utils.models import Relay, MetaData
from captchamonitor.utils.onionoo import Onionoo, OnionooRelayEntry
from captchamonitor.utils.collector import Collector
from captchamonitor.utils.consensus_parser import ConsensusV3Parser, ConsensusRelayEntry


class UpdateRelays:
    """
    Fetches the latest consensus and inserts the relays listed there into the
    database
    """

    def __init__(
        self,
        config: Config,
        db_session: sessionmaker,
        auto_update: bool = True,
    ) -> None:
        """
        Initializes UpdateRelays

        :param config: The config class instance that contains global configuration values
        :type config: Config
        :param db_session: Database session used to connect to the database
        :type db_session: sessionmaker
        :param auto_update: Should I update the relay list when __init__ is called, defaults to True
        :type auto_update: bool
        """
        # Private class attributes
        self.__logger = logging.getLogger(__name__)
        self.__config: Config = config
        self.__db_session: sessionmaker = db_session
        self.__collector: Collector = Collector()
        self.__datetime_format: str = "%Y-%m-%d-%H-00-00"

        self.__check_last_relay_update()

        if auto_update:
            if self.__hours_since_last_update() >= 1:
                self.__logger.info("Updating the relay list using the latest consensus")
                self.update()
            else:
                self.__logger.info(
                    "Did not update the relay list since less than an hour passed since last update"
                )

    def __hours_since_last_update(self) -> int:
        """
        Calculates the number of hours passed since the last relay update

        :return: Number of hours passed since last relay update
        :rtype: int
        """
        current_datetime = datetime.now().replace(minute=0, second=0, microsecond=0)
        last_datetime = self.__check_last_relay_update()
        time_difference = current_datetime - last_datetime
        return int(time_difference.total_seconds() // 3600)

    def __check_last_relay_update(self) -> datetime:
        """
        Connects to the database and check the last time relays were updated

        :return: The last time relays were updated
        :rtype: datetime
        """
        metadata_key = "last_relay_update_datetime"

        query = self.__db_session.query(MetaData).filter(MetaData.key == metadata_key)

        # Check if it exists in the database
        if query.count() == 0:
            # Create a new one if it doesn't exist
            current_datetime = datetime.now()
            current_datetime_str = current_datetime.strftime(self.__datetime_format)
            metadata = MetaData(
                key=metadata_key,
                value=current_datetime_str,
            )
            self.__db_session.add(metadata)
            return datetime.strptime(current_datetime_str, self.__datetime_format)

        # Get and return the existing value
        date_from_db = query.one().value
        return datetime.strptime(date_from_db, self.__datetime_format)

    def __insert_batch_into_db(
        self,
        onionoo_relay_data: List[OnionooRelayEntry],
        parsed_consensus: Dict[str, ConsensusRelayEntry],
    ) -> None:
        """
        Inserts given batch of data into the database

        :param onionoo_relay_data: List of OnionooRelayEntry objects
        :type onionoo_relay_data: List[OnionooRelayEntry]
        :param parsed_consensus: Dictionary of ConsensusRelayEntry
        :type parsed_consensus: Dict[str, ConsensusRelayEntry]
        """
        # Iterate over the relays in consensus file
        for onionoo_relay in onionoo_relay_data:

            db_relay = Relay(
                fingerprint=onionoo_relay.fingerprint,
                ipv4_address=parsed_consensus[onionoo_relay.fingerprint].IP,
                ipv6_address=parsed_consensus[onionoo_relay.fingerprint].IPv6,
                ipv4_exiting_allowed=onionoo_relay.ipv4_exiting_allowed,
                ipv6_exiting_allowed=onionoo_relay.ipv6_exiting_allowed,
                country=onionoo_relay.country,
                country_name=onionoo_relay.country_name,
                continent=onionoo_relay.continent,
                status=True,
                nickname=onionoo_relay.nickname,
                first_seen=onionoo_relay.first_seen,
                last_seen=onionoo_relay.last_seen,
                version=onionoo_relay.version,
                asn=onionoo_relay.asn,
                asn_name=onionoo_relay.asn_name,
                platform=onionoo_relay.platform,
            )

            # Add to the database
            self.__db_session.add(db_relay)

        # Commit changes to the database
        self.__db_session.commit()

    def update(self, batch_size: int = 30) -> None:
        """
        Gets the latest consensus and parses the list of relays in the consensus.
        Later, adds the relays to the database. Performs this operation in batches
        to not to overwhelm the Onionoo API.

        :param batch_size: Number of relays to process in a single batch, defaults to 30
        :type batch_size: int
        """
        # Download the latest consensus
        current_datetime = datetime.now()
        consensus_file = self.__collector.get_consensus(current_datetime)

        # Parse the consensus file
        parsed_consensus = {
            str(relay.fingerprint): relay
            for relay in ConsensusV3Parser(consensus_file).relay_entries
        }

        relay_fingerprints = list(parsed_consensus.keys())

        # Get relay information in chunks to not overwhelm Onionoo API
        for i in range(0, len(relay_fingerprints), batch_size):
            relay_batch = relay_fingerprints[i : i + batch_size]

            # Get relays' details from Onionoo
            onionoo_relay_data = Onionoo(relay_batch).relay_entries

            self.__insert_batch_into_db(onionoo_relay_data, parsed_consensus)
