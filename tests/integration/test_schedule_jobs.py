import unittest

from captchamonitor.utils.config import Config
from captchamonitor.utils.models import Relay, Domain, Fetcher, FetchQueue
from captchamonitor.utils.database import Database
from captchamonitor.core.schedule_jobs import ScheduleJobs


class TestScheduleJobs(unittest.TestCase):
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

        domain_1 = Domain(
            domain="check.torproject.org",
            supports_http=True,
            supports_https=True,
            supports_ftp=False,
            supports_ipv4=True,
            supports_ipv6=False,
            requires_multiple_requests=True,
        )

        domain_2 = Domain(
            domain="duckduckgo.com",
            supports_http=True,
            supports_https=True,
            supports_ftp=False,
            supports_ipv4=True,
            supports_ipv6=False,
            requires_multiple_requests=True,
        )

        test_relay = Relay(
            fingerprint="A53C46F5B157DD83366D45A8E99A244934A14C46",
            ipv4_address="128.31.0.13",
            ipv4_exiting_allowed=True,
            ipv6_exiting_allowed=False,
        )

        test_fetcher_non_tor = Fetcher(
            method="firefox_browser", uses_tor=False, version="82"
        )

        test_fetcher_tor = Fetcher(method="tor_browser", uses_tor=True, version="82")

        # Commit changes to the database
        self.db_session.add(domain_1)
        self.db_session.add(domain_2)
        self.db_session.add(test_relay)
        self.db_session.add(test_fetcher_non_tor)
        self.db_session.add(test_fetcher_tor)
        self.db_session.commit()

        self.schedule_jobs = ScheduleJobs(
            config=self.config,
            db_session=self.db_session,
            loop=False,
        )

        self.db_fetch_queue_query = self.db_session.query(FetchQueue)

    def tearDown(self):
        self.db_session.close()

    def test_schedule_jobs_init(self):
        # Make sure the table is empty
        self.assertEqual(self.db_fetch_queue_query.count(), 0)

        # Schedule jobs
        self.schedule_jobs.schedule_next_batch()

        # Check if jobs are scheduled
        self.assertEqual(self.db_fetch_queue_query.count(), 4)
