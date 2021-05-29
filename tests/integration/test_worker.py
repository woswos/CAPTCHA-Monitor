import pytest
import unittest
from captchamonitor.utils.config import Config
from captchamonitor.core.worker import Worker
from captchamonitor.utils.database import Database
from captchamonitor.utils.models import (
    URL,
    Relay,
    Fetcher,
    FetchQueue,
    FetchFailed,
    FetchCompleted,
)


class TestWorker(unittest.TestCase):
    def setUp(self):
        self.config = Config()
        self.database = Database(
            self.config["db_host"],
            self.config["db_port"],
            self.config["db_name"],
            self.config["db_user"],
            self.config["db_password"],
        )
        self.db_session = self.database.session()
        self.worker_id = "0"
        self.worker = Worker(
            worker_id=self.worker_id,
            config=self.config,
            db_session=self.db_session,
            loop=False,
        )

        # Add test urls
        test_url_success = URL(
            url="https://check.torproject.org/",
            supports_http=True,
            supports_https=True,
            supports_ftp=False,
            supports_ipv4=True,
            supports_ipv6=False,
            requires_multiple_requests=True,
        )
        self.db_session.add(test_url_success)

        test_url_fail = URL(
            url="https://StupidURL",
            supports_http=True,
            supports_https=True,
            supports_ftp=False,
            supports_ipv4=True,
            supports_ipv6=False,
            requires_multiple_requests=True,
        )
        self.db_session.add(test_url_fail)

        # Add test relay
        test_relay = Relay(
            fingerprint="A53C46F5B157DD83366D45A8E99A244934A14C46",
            ipv4_address="128.31.0.13",
            ipv4_exiting_allowed=True,
            ipv6_exiting_allowed=False,
        )
        self.db_session.add(test_relay)

        # Add test fetchers
        test_fetcher_non_tor = Fetcher(
            method="firefox_browser", uses_tor=False, version="82"
        )
        self.db_session.add(test_fetcher_non_tor)

        test_fetcher_tor = Fetcher(
            method="firefox_browser", uses_tor=True, version="82"
        )
        self.db_session.add(test_fetcher_tor)

        # Commit changes to the database
        self.db_session.commit()

    def tearDown(self):
        self.db_session.close()

    def test_worker_single_run_without_tor_success(self):
        # Insert a job
        new_job = FetchQueue(fetcher_id=1, url_id=1, relay_id=1)
        self.db_session.add(new_job)

        # Commit changes to the database
        self.db_session.commit()

        # Check successful jobs
        db_job = self.db_session.query(FetchCompleted)
        self.assertEqual(db_job.count(), 0)

        # Process the job
        self.worker.process_next_job()

        self.assertNotEqual(db_job.count(), 0)
        self.assertEqual(db_job.first().ref_url.url, "https://check.torproject.org/")

    def test_worker_single_run_without_tor_fail(self):
        # Insert a job
        new_job = FetchQueue(fetcher_id=1, url_id=2, relay_id=1)
        self.db_session.add(new_job)

        # Commit changes to the database
        self.db_session.commit()

        # Check failed jobs
        db_job = self.db_session.query(FetchFailed)
        self.assertEqual(db_job.count(), 0)

        # Process the job
        self.worker.process_next_job()

        self.assertNotEqual(db_job.count(), 0)
        self.assertEqual(db_job.first().ref_url.url, "https://StupidURL")

    def test_worker_single_run_with_tor_success(self):
        # Insert a job
        new_job = FetchQueue(fetcher_id=2, url_id=1, relay_id=1)
        self.db_session.add(new_job)

        # Commit changes to the database
        self.db_session.commit()

        # Check successful jobs
        db_job = self.db_session.query(FetchCompleted)
        self.assertEqual(db_job.count(), 0)

        # Process the job
        self.worker.process_next_job()

        self.assertNotEqual(db_job.count(), 0)
        self.assertEqual(db_job.first().ref_url.url, "https://check.torproject.org/")

    def test_worker_single_run_with_tor_fail(self):
        # Insert a job
        new_job = FetchQueue(fetcher_id=2, url_id=2, relay_id=1)
        self.db_session.add(new_job)

        # Commit changes to the database
        self.db_session.commit()

        # Check failed jobs
        db_job = self.db_session.query(FetchFailed)
        self.assertEqual(db_job.count(), 0)

        # Process the job
        self.worker.process_next_job()

        self.assertNotEqual(db_job.count(), 0)
        self.assertEqual(db_job.first().ref_url.url, "https://StupidURL")

    def test_worker_no_job_in_queue(self):
        # Process the job, shouldn't rise any errors
        self.worker.process_next_job()
