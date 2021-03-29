import sys
import logging
from captchamonitor.utils.config import Config
from captchamonitor.utils.database import Database
from captchamonitor.utils.exceptions import DatabaseInitError, ConfigInitError


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

            self.db = Database(
                self.config["db_host"],
                self.config["db_port"],
                self.config["db_name"],
                self.config["db_user"],
                self.config["db_password"],
                verbose,
            )

        except (DatabaseInitError, ConfigInitError) as e:
            self.logger.warning(
                "Could not initialize CAPTCHA Monitor, exitting"
            )
            sys.exit(1)

        # Obtain the session from database module
        self.session = self.db.session()

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
