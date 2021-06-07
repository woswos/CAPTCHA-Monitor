import sys
import time
import logging
from typing import Optional

from captchamonitor.core.worker import Worker
from captchamonitor.utils.config import Config
from captchamonitor.utils.database import Database
from captchamonitor.utils.exceptions import ConfigInitError, DatabaseInitError
from captchamonitor.core.update_relays import UpdateRelays
from captchamonitor.core.update_website import UpdateWebsite
from captchamonitor.utils.small_scripts import node_id


class CaptchaMonitor:
    """
    The main high level class for putting different modules together
    """

    def __init__(self, verbose: Optional[bool] = False) -> None:
        """
        Initializes the submodules

        :param verbose: Verbose output option, defaults to False
        :type verbose: bool, optional
        """
        # Private class attributes
        self.__logger = logging.getLogger(__name__)
        self.__node_id: str = str(node_id())

        try:
            self.__config: Config = Config()

        except ConfigInitError:
            self.__logger.warning(
                "Could not initialize CAPTCHA Monitor since some configuration values are missing, exitting"
            )
            sys.exit(1)

        # Try connecting to the database 3 times
        for _ in range(3):
            try:
                self.__database: Database = Database(
                    self.__config["db_host"],
                    self.__config["db_port"],
                    self.__config["db_name"],
                    self.__config["db_user"],
                    self.__config["db_password"],
                    verbose,
                )
                break
            except DatabaseInitError:
                self.__logger.warning("Could not connect to the database, retrying")
                time.sleep(3)

        # Check if database connection was made
        if not hasattr(self, f"_{self.__class__.__name__}__database"):
            self.__logger.warning(
                "Could not initialize CAPTCHA Monitor since I couldn't connect to the database, exitting"
            )
            sys.exit(1)

        # Obtain the session from database module
        self.__db_session = self.__database.session()

    def add_jobs(self) -> None:
        """
        Adds new jobs to the database
        """
        self.__logger.info("Adding new jobs")

    def worker(self) -> None:
        """
        Fetches a job from the database and processes it using Tor Browser or
        other specified browsers. Inserts the result back into the database.
        """
        self.__logger.info("Running worker %s", self.__node_id)

        Worker(
            worker_id=self.__node_id,
            config=self.__config,
            db_session=self.__db_session,
        )

    def update_urls(self) -> None:
        """
        Updates the list of URLs in the database
        """
        self.__logger.info("Started updating URLs")

        UpdateWebsite(config=self.__config, db_session=self.__db_session)

    def update_relays(self) -> None:
        """
        Updates the list of relays in the database
        """
        self.__logger.info("Started updating relays")

        UpdateRelays(config=self.__config, db_session=self.__db_session)

    def analyze(self) -> None:
        """
        Analyses the data recorded in the database
        """
        self.__logger.debug("Started data analysis")

    def __del__(self) -> None:
        """
        Do cleaning before going out of scope
        """
        if hasattr(self, "__db_session"):
            self.__db_session.close()
