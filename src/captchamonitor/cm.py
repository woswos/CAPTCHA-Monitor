import sys
import time
import logging
from captchamonitor.utils.config import Config
from captchamonitor.utils.database import Database
from captchamonitor.utils.exceptions import DatabaseInitError, ConfigInitError
from captchamonitor.core.worker import Worker


class CaptchaMonitor:
    """
    The main high level class for putting different modules together
    """

    def __init__(self, verbose=False):
        """
        Initializes the submodules

        :param verbose: Verbose output option, defaults to False
        :type verbose: bool, optional
        """
        self.logger = logging.getLogger(__name__)

        try:
            self.config = Config()

        except ConfigInitError:
            self.logger.warning(
                "Could not initialize CAPTCHA Monitor since some configuration values are missing, exitting"
            )
            sys.exit(1)

        # Try connecting to the database 3 times
        for _ in range(3):
            try:
                self.database = Database(
                    self.config["db_host"],
                    self.config["db_port"],
                    self.config["db_name"],
                    self.config["db_user"],
                    self.config["db_password"],
                    verbose,
                )
                break
            except DatabaseInitError:
                self.logger.warning("Could not connect to the database, retrying")
                time.sleep(3)

        # Check if database connection was made
        if not hasattr(self, "database"):
            self.logger.warning(
                "Could not initialize CAPTCHA Monitor since I couldn't connect to the database, exitting"
            )
            sys.exit(1)

        # Obtain the session from database module
        self.db_session = self.database.session()

    def add_jobs(self):
        """
        Adds new jobs to the database
        """
        self.logger.debug("Adding new jobs")

    def worker(self):
        """
        Fetches a job from the database and processes it using Tor Browser or
        other specified browsers. Inserts the result back into the database.
        """
        self.logger.debug("Running worker")

        Worker(worker_id="0", config=self.config, db_session=self.db_session)

    def update_urls(self):
        """
        Updates the list of URLs in the database
        """
        self.logger.debug("Started updating URLs")

    def analyze(self):
        """
        Analyses the data recorded in the database
        """
        self.logger.debug("Started data analysis")

    def __del__(self):
        """
        Do cleaning before going out of scope
        """
        self.db_session.close()
