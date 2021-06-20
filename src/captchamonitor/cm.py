import sys
import time
import logging
from typing import Optional

from captchamonitor.core.worker import Worker
from captchamonitor.utils.config import Config
from captchamonitor.core.analyzer import Analyzer
from captchamonitor.utils.database import Database
from captchamonitor.utils.exceptions import ConfigInitError, DatabaseInitError
from captchamonitor.core.schedule_jobs import ScheduleJobs
from captchamonitor.core.update_relays import UpdateRelays
from captchamonitor.core.update_domains import UpdateDomains
from captchamonitor.utils.small_scripts import node_id
from captchamonitor.core.update_fetchers import UpdateFetchers


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

    def update_domains(self) -> None:
        """
        Updates the list of domains in the database
        """
        self.__logger.info("Started updating domains")

        UpdateDomains(config=self.__config, db_session=self.__db_session)

    def update_relays(self) -> None:
        """
        Updates the list of relays in the database
        """
        self.__logger.info("Started updating relays")

        UpdateRelays(config=self.__config, db_session=self.__db_session)

    def update_fetchers(self) -> None:
        """
        Updates the list of fetchers in the database
        """
        self.__logger.info("Started updating list of fetchers")

        UpdateFetchers(config=self.__config, db_session=self.__db_session)

    def schedule_jobs(self) -> None:
        """
        Adds new jobs to the database
        """
        self.__logger.info("Scheduling new jobs")

        ScheduleJobs(
            config=self.__config,
            db_session=self.__db_session,
            loop=False,
        ).schedule_next_batch()

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

    def analyzer(self) -> None:
        """
        Analyzes the data recorded in the database
        """
        self.__logger.debug("Started data analysis")

        Analyzer(
            analyzer_id=self.__node_id,
            config=self.__config,
            db_session=self.__db_session,
        )

    def __del__(self) -> None:
        """
        Do cleaning before going out of scope
        """
        if hasattr(self, "__db_session"):
            self.__db_session.close()
