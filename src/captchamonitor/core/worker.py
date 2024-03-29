import time
import logging
from typing import Union, Optional

from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from captchamonitor.utils.config import Config
from captchamonitor.utils.models import FetchQueue, FetchFailed, FetchCompleted
from captchamonitor.utils.exceptions import FetcherNotFound
from captchamonitor.utils.tor_launcher import TorLauncher
from captchamonitor.utils.small_scripts import (
    hasattr_private,
    get_traceback_information,
)
from captchamonitor.fetchers.tor_browser import TorBrowser
from captchamonitor.fetchers.opera_browser import OperaBrowser
from captchamonitor.fetchers.chrome_browser import ChromeBrowser
from captchamonitor.utils.container_manager import ContainerManager
from captchamonitor.fetchers.firefox_browser import FirefoxBrowser


class Worker:
    """
    Fetches a job from the database and processes it using Tor Browser or
    other specified browsers. Inserts the result back into the database.
    Keeps doing this until the kill signal is received or the program exits.
    """

    def __init__(
        self,
        worker_id: str,
        config: Config,
        db_session: sessionmaker,
        loop: Optional[bool] = True,
    ) -> None:
        """
        Initializes a new worker

        :param worker_id: Worker ID assigned for this worker
        :type worker_id: str
        :param config: The config class instance that contains global configuration values
        :type config: Config
        :param db_session: Database session used to connect to the database
        :type db_session: sessionmaker
        :param loop: Should I process a single job or loop over all jobs, defaults to True
        :type loop: bool, optional
        """
        # Private class attributes
        self.__logger = logging.getLogger(__name__)
        self.__config: Config = config
        self.__db_session: sessionmaker = db_session
        self.__worker_id: str = worker_id
        self.__tor_launcher: TorLauncher = TorLauncher(self.__config)
        self.__job_queue_delay: float = float(self.__config["job_queue_delay"])
        self.__fetcher: Union[TorBrowser, FirefoxBrowser, ChromeBrowser, OperaBrowser]

        # Loop over the jobs
        while loop:
            self.process_next_job()
            time.sleep(self.__job_queue_delay)

    def process_next_job(self) -> None:
        """
        Processes the next available job in the job queue. Claims the job, tries
        fetching the URL specified in the job with the specified fetcher. If
        successfull, inserts the results into the FetchCompleted table. Otherwise,
        inserts the results into the FetchFailed table. Finally, removes the
        claimed job from the queue.

        :raises FetcherNotFound: If requested fetcher is not available
        """
        # pylint: disable=R0912,R0915
        # Get claimed jobs by this worker
        db_job = self.__db_session.query(FetchQueue).filter(
            FetchQueue.claimed_by == self.__worker_id
        )

        # Claim a new job if not already claimed
        if db_job.count() == 0:
            # TODO: Yes, the following is a bad practice, please use an ORM statement instead
            table = FetchQueue.__tablename__.lower()
            query = f"UPDATE {table} SET claimed_by = :worker_id WHERE id = (SELECT min(id) FROM {table} WHERE claimed_by IS NULL)"
            params = {"worker_id": self.__worker_id}
            self.__db_session.execute(text(query), params)
            self.__db_session.commit()

        # Get the claimed job
        job = db_job.first()

        # Don't do anything if there is no job in the queue
        if job is None:
            return

        try:
            # Create the options based on the ones described within the job
            options_dict = {}
            if job.options is not None:
                options_dict = job.options

            # Create a new circuit if we will be using Tor
            proxy = None
            if job.ref_fetcher.uses_proxy_type == "tor":
                self.__tor_launcher.create_new_circuit_to(job.ref_relay.fingerprint)
                proxy = (
                    self.__tor_launcher.ip_address,
                    self.__tor_launcher.socks_port,
                )

            # Check if the proxy type is http, if so: add host and port into the proxy tuple
            elif job.ref_fetcher.uses_proxy_type == "http":
                proxy = (job.ref_proxy.host, job.ref_proxy.port)

            # Fetch it using a fetcher
            if job.ref_fetcher.method == TorBrowser.method_name_in_db:
                options_dict.update({"tbb_security_level": job.tbb_security_level})
                self.__fetcher = TorBrowser(
                    config=self.__config,
                    url=job.url,
                    proxy=proxy,
                    options=options_dict,
                    use_proxy_type=job.ref_fetcher.uses_proxy_type,
                )

            elif job.ref_fetcher.method == FirefoxBrowser.method_name_in_db:
                self.__fetcher = FirefoxBrowser(
                    config=self.__config,
                    url=job.url,
                    proxy=proxy,
                    options=options_dict,
                    use_proxy_type=job.ref_fetcher.uses_proxy_type,
                )

            elif job.ref_fetcher.method == ChromeBrowser.method_name_in_db:
                self.__fetcher = ChromeBrowser(
                    config=self.__config,
                    url=job.url,
                    proxy=proxy,
                    options=options_dict,
                    use_proxy_type=job.ref_fetcher.uses_proxy_type,
                )

            elif job.ref_fetcher.method == OperaBrowser.method_name_in_db:
                self.__fetcher = OperaBrowser(
                    config=self.__config,
                    url=job.url,
                    proxy=proxy,
                    options=options_dict,
                    use_proxy_type=job.ref_fetcher.uses_proxy_type,
                )

            else:
                raise FetcherNotFound

            self.__fetcher.setup()
            self.__fetcher.connect()
            self.__fetcher.fetch()

        # pylint: disable=W0703
        except Exception:
            error = get_traceback_information()

            # If failed, put into the failed table
            failed = FetchFailed(
                url=job.url,
                options=options_dict,
                tbb_security_level=job.tbb_security_level,
                captcha_monitor_version=self.__config["version"],
                fail_reason=str(error),
                fetcher_id=job.fetcher_id,
                domain_id=job.domain_id,
                relay_id=job.relay_id,
                proxy_id=job.proxy_id,
            )
            self.__db_session.add(failed)
            self.__logger.debug(
                "Worker %s wasn't able to fetch %s with %s: %s",
                self.__worker_id,
                job.url,
                job.fetcher_id,
                str(error),
            )

            # If fetcher was initialized correctly
            if hasattr_private(self, "__fetcher"):
                # Check if container is healthy
                self.__logger.debug("Checking if the container is healthy")
                ContainerManager(
                    self.__fetcher.container_host
                ).restart_browser_container_if_unhealthy()

        else:
            # If successful, put into the completed table
            completed = FetchCompleted(
                url=job.url,
                options=options_dict,
                tbb_security_level=job.tbb_security_level,
                captcha_monitor_version=self.__config["version"],
                html_data=self.__fetcher.page_source,
                http_requests=self.__fetcher.page_har,
                fetcher_id=job.fetcher_id,
                domain_id=job.domain_id,
                relay_id=job.relay_id,
                proxy_id=job.proxy_id,
            )
            self.__db_session.add(completed)
            self.__logger.debug(
                "Worker %s successfully fetched %s with %s",
                self.__worker_id,
                job.url,
                job.fetcher_id,
            )

        finally:
            # Close the fetcher
            if hasattr_private(self, "__fetcher"):
                self.__fetcher.close()

            # Reset the changes
            self.__tor_launcher.reset_configuration()

            # Delete job from the job queue
            self.__db_session.delete(job)

            # Commit changes to the database
            self.__db_session.commit()

    def __del__(self) -> None:
        """
        Perform cleanup before going out of scope
        """
        if hasattr_private(self, "__tor_launcher"):
            # Stop the containers
            self.__tor_launcher.close()
