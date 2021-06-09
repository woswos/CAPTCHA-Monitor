import unittest

from captchamonitor.core.worker import Worker
from captchamonitor.utils.config import Config
from captchamonitor.utils.models import (
    Relay,
    Domain,
    Fetcher,
    FetchQueue,
    FetchCompleted,
)
from captchamonitor.core.analyzer import Analyzer
from captchamonitor.utils.database import Database


class TestAnalyzer(unittest.TestCase):
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

        self.analyzer_id = "0"

        self.test_domain = "duckduckgo.com"

        self.worker = Worker(
            worker_id="0",
            config=self.config,
            db_session=self.db_session,
            loop=False,
        )

        domain = Domain(
            domain=self.test_domain,
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

        queue_non_tor = FetchQueue(
            url=f"https://www.{self.test_domain}",
            fetcher_id=1,
            domain_id=1,
        )

        queue_tor = FetchQueue(
            url=f"https://www.{self.test_domain}",
            fetcher_id=2,
            domain_id=1,
            relay_id=1,
        )

        # Commit changes to the database
        self.db_session.add(domain)
        self.db_session.add(test_relay)
        self.db_session.add(test_fetcher_non_tor)
        self.db_session.add(test_fetcher_tor)
        self.db_session.add(queue_non_tor)
        self.db_session.add(queue_tor)
        self.db_session.commit()

        # Process the non tor job
        self.worker.process_next_job()

        # Process the tor job
        self.worker.process_next_job()

        # Make sure that the jobs are processed
        self.assertEqual(self.db_session.query(FetchCompleted).count(), 2)

    def tearDown(self):
        self.db_session.close()

    def test_analyzer_init(self):
        Analyzer(
            analyzer_id=self.analyzer_id,
            config=self.config,
            db_session=self.db_session,
        )
