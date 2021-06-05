import logging
from datetime import datetime

from sqlalchemy.orm import sessionmaker

from captchamonitor.utils.config import Config
from captchamonitor.utils.models import MetaData
from captchamonitor.utils.collector import Collector


class UpdateRelays:
    """
    Fetches the latest consensus and inserts the relays listed there into the
    database
    """

    def __init__(
        self,
        config: Config,
        db_session: sessionmaker,
    ) -> None:
        # Private class attributes
        self.__logger = logging.getLogger(__name__)
        self.__config: Config = config
        self.__db_session: sessionmaker = db_session
        self.__collector: Collector = Collector()
        self.__datetime_format: str = "%Y-%m-%d-%H-00-00"
        self.__current_datetime: datetime
        self.__current_datetime_str: str

        # Execute the private methods
        self.__update_current_time()

    def __update_current_time(self) -> None:
        """
        Updates the current time
        """
        self.__current_datetime = datetime.now().strftime(
            self.__datetime_format
        )
        self.__current_datetime_str = self.__current_datetime.strftime(
            self.__datetime_format
        )

    def __check_last_relay_update(self) -> datetime:
        """
        Connects to the database and check the last time relays were updated

        :return: The last time relays were updated
        :rtype: datetime
        """
        metadata_key = "last_relay_update_datetime"

        query = self.__db_session.query(MetaData).filter(
            MetaData.key == metadata_key
        )

        # Check if it exists in the database
        if query.count() == 0:
            # Create a new one if it doesn't exist'
            metadata = MetaData(
                key=metadata_key, value=self.__current_datetime_str
            )
            self.__db_session.add(metadata)
            return datetime.strptime(
                self.__current_datetime_str, self.__datetime_format
            )

        else:
            # Get and return the existing value
            date = query.one().value
            return datetime.strptime(date, self.__datetime_format)
