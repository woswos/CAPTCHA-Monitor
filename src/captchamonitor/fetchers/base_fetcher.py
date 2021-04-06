import logging


class BaseFetcher:
    """
    Base fetcher class that will inherited by the actual fetchers, used to unify
    the fetcher interfaces
    """

    def __init__(
        self, config, url, tor_launcher, timeout=30, options=None, use_tor=True
    ):
        """
        Initializes the fetcher with given arguments and tries to fetch the given
        URL

        :param url: The URL to fetch
        :type url: str
        :param tor_launcher: TorLauncher class
        :type tor_launcher: TorLauncher class
        :param timeout: Maximum time allowed for a web page to load, defaults to 30
        :type timeout: int, optional
        :param options: Dictionary of options to pass to the fetcher, defaults to None
        :type options: dict, optional
        :param use_tor: Should I connect the fetcher to Tor? Has no effect when using Tor Browser, defaults to True
        :type use_tor: bool, optional
        """
        # Public attributes
        self.url = url
        self.use_tor = use_tor
        self.timeout = timeout
        self.options = options
        self.driver = None

        # Other required attributes
        self.tor_launcher = tor_launcher
        self.config = config
        self.selenium_options = None

        self.logger = logging.getLogger(__name__)

    def __del__(self):
        if self.driver is not None:
            self.driver.quit()
