import logging
from captchamonitor.utils.tor_launcher import TorLauncher
from captchamonitor.fetchers.tor_browser import TorBrowser


class Worker:
    """
    Fetches a job from the database and processes it using Tor Browser or
    other specified browsers. Inserts the result back into the database.
    Keeps doing this until the kill signal is received or the program exits.
    """

    def __init__(self, worker_id, config, db_session):
        """
        Initializes a new worker
        """
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.db_session = db_session

        self.tor_launcher = TorLauncher(self.config)

        options = {"TorBrowserSecurityLevel": "standard"}
        test = TorBrowser(
            config=self.config,
            url="https://check.torproject.org/",
            tor_launcher=self.tor_launcher,
            options=options,
        )
        test.setup()
        test.connect()

        print(worker_id, test.fetch())

        # while True:

        #     # Claim job and get job

        #     # Fetch it

        #     # If failed, put into failed

        #     # If successful, put into results
