import logging
from captchamonitor.utils.tor_launcher import TorLauncher


class Worker:
    """
    Fetches a job from the database and processes it using Tor Browser or
    other specified browsers. Inserts the result back into the database.
    """

    def __init__(self, config, db_session):
        """
        Initializes a new worker
        """
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.db_session = db_session

        self.tor_launcher = TorLauncher(self.config)
