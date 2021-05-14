import logging
from sqlalchemy import text
from captchamonitor.utils.models import FetchQueue, FetchFailed, FetchCompleted
from captchamonitor.utils.tor_launcher import TorLauncher
from captchamonitor.fetchers.tor_browser import TorBrowser
from captchamonitor.fetchers.firefox_browser import FirefoxBrowser
from captchamonitor.fetchers.chrome_fetcher import ChromeBrowser
from captchamonitor.utils.exceptions import FetcherNotFound


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
        self.worker_id = worker_id
        self.tor_launcher = TorLauncher(self.config)

        # Loop over the jobs
        self.__process_next_job()

    def __process_next_job(self):
        """
        Processes the next available job in the job queue. Claims the job, tries
        fetching the URL specified in the job with the specified fetcher. If
        successfull, inserts the results into the FetchCompleted table. Otherwise,
        inserts the results into the FetchFailed table. Finally, removes the
        claimed job from the queue.
        """
        # Get claimed jobs by this worker
        db_job = self.db_session.query(FetchQueue).filter(
            FetchQueue.claimed_by == self.worker_id
        )

        # Claim a new job if not already claimed
        if db_job.count() == 0:
            # TODO: Yes, the following is a bad practice, please use an ORM statement instead
            table = FetchQueue.__tablename__.lower()
            query = f"UPDATE {table} SET claimed_by = :worker_id WHERE id = (SELECT min(id) FROM {table} WHERE claimed_by IS NULL)"
            params = {"worker_id": self.worker_id}
            self.db_session.execute(text(query), params)
            self.db_session.commit()

        # Get the claimed job
        job = db_job.first()

        # Don't do anything if there is no job in the queue
        if job is None:
            return

        # Fetch it using a fetcher
        try:
            if job.ref_fetcher.method == TorBrowser.method_name_in_db:
                options_dict = {"TorBrowserSecurityLevel": job.tbb_security_level}
                if job.options is not None:
                    options_dict.update(job.options)
                fetcher = TorBrowser(
                    config=self.config,
                    url=job.ref_url.url,
                    tor_launcher=self.tor_launcher,
                    options=options_dict,
                    use_tor=job.ref_fetcher.uses_tor,
                )

            elif job.ref_fetcher.method == FirefoxBrowser.method_name_in_db:
                fetcher = FirefoxBrowser(
                    config=self.config,
                    url=job.ref_url.url,
                    tor_launcher=self.tor_launcher,
                    options=job.options,
                    use_tor=job.ref_fetcher.uses_tor,
                )

            elif job.ref_fetcher.method == ChromeBrowser.method_name_in_db:
                fetcher = ChromeBrowser(
                    config=self.config,
                    url=job.ref_url.url,
                    tor_launcher=self.tor_launcher,
                    options=job.options,
                    use_tor=job.ref_fetcher.uses_tor,
                )

            else:
                raise FetcherNotFound

            fetcher.setup()
            fetcher.connect()
            fetcher.fetch()

        # pylint: disable=W0703
        except Exception as exception:
            # If failed, put into the failed table
            failed = FetchFailed(
                options=job.options,
                tbb_security_level=job.tbb_security_level,
                captcha_monitor_version=self.config["version"],
                fail_reason=str(exception),
                target_fetcher=job.target_fetcher,
                url_id=job.url_id,
                relay_fingerprint=job.relay_fingerprint,
            )
            self.db_session.add(failed)
            self.logger.debug(
                "Worker %s wasn't able to fetch URL id %s with %s: %s",
                self.worker_id,
                job.url_id,
                job.target_fetcher,
                str(exception),
            )

        else:
            # If successful, put into the completed table
            completed = FetchCompleted(
                options=job.options,
                tbb_security_level=job.tbb_security_level,
                captcha_monitor_version=self.config["version"],
                html_data=fetcher.page_source,
                http_requests=fetcher.page_har,
                target_fetcher=job.target_fetcher,
                url_id=job.url_id,
                relay_fingerprint=job.relay_fingerprint,
            )
            self.db_session.add(completed)
            self.logger.debug(
                "Worker %s successfully fetched URL id %s with %s",
                self.worker_id,
                job.url_id,
                job.target_fetcher,
            )

        finally:
            # Delete job from the job queue
            self.db_session.delete(job)

            # Commit changes to the database
            self.db_session.commit()
