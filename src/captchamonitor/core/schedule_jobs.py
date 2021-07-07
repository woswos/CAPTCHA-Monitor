import time
import logging
from typing import Optional

from sqlalchemy.orm import sessionmaker

from captchamonitor.utils.config import Config
from captchamonitor.utils.models import Relay, Domain, Fetcher, FetchQueue


class ScheduleJobs:
    """
    Uses the list of domains, fetchers, and relays to inteligently schedule new
    jobs for workers to process.
    """

    def __init__(
        self,
        config: Config,
        db_session: sessionmaker,
        loop: Optional[bool] = True,
    ):
        """
        Initializes a new job scheduler

        :param config: The config class instance that contains global configuration values
        :type config: Config
        :param db_session: Database session used to connect to the database
        :type db_session: sessionmaker
        :param loop: Should I keep adding multiple batches of jobs, defaults to True
        :type loop: bool, optional
        """
        # Private class attributes
        self.__logger = logging.getLogger(__name__)  # pylint: disable=W0238
        self.__config: Config = config
        self.__db_session: sessionmaker = db_session
        self.__job_queue_delay: float = float(self.__config["job_queue_delay"])

        # Loop over the jobs
        while loop:
            self.schedule_next_batch()
            time.sleep(self.__job_queue_delay)

    def schedule_next_batch(self) -> None:
        """
        Goes over all available domains and inserts a new job for fetching them
        with Tor Browser and Firefox Browser
        """
        # pylint: disable=C0121
        # Get the list of domains
        domains = self.__db_session.query(Domain).all()
        tor_browser = (
            self.__db_session.query(Fetcher)
            .filter(Fetcher.method == "tor_browser")
            .filter(Fetcher.uses_proxy_type == "tor")
            .first()
        )
        firefox_browser = (
            self.__db_session.query(Fetcher)
            .filter(Fetcher.method == "firefox_browser")
            .filter(Fetcher.uses_proxy_type == None)
            .first()
        )
        relay = (
            self.__db_session.query(Relay)
            .filter(Relay.ipv4_exiting_allowed == True)
            .first()
        )

        for domain in domains:
            new_job_tor_browser = FetchQueue(
                url=f"https://{domain.domain}",
                options=domain.options,
                fetcher_id=tor_browser.id,
                domain_id=domain.id,
                relay_id=relay.id,
            )
            new_job_firefox_browser = FetchQueue(
                url=f"https://{domain.domain}",
                options=domain.options,
                fetcher_id=firefox_browser.id,
                domain_id=domain.id,
            )
            self.__db_session.add(new_job_tor_browser)
            self.__db_session.add(new_job_firefox_browser)

        # Save changes
        self.__db_session.commit()
