# pylint: disable=C0115,C0116,W0212

import pytest

from captchamonitor.core.worker import Worker
from captchamonitor.utils.models import (
    Relay,
    Domain,
    Fetcher,
    FetchQueue,
    FetchFailed,
    FetchCompleted,
)


@pytest.fixture()
def insert_relay_and_domain(db_session):
    # Add test urls
    test_domain_success = Domain(
        domain="check.torproject.org",
        supports_http=True,
        supports_https=True,
        supports_ftp=False,
        supports_ipv4=True,
        supports_ipv6=False,
        requires_multiple_requests=True,
    )
    db_session.add(test_domain_success)

    test_domain_fail = Domain(
        domain="stupid.urlextension",
        supports_http=True,
        supports_https=True,
        supports_ftp=False,
        supports_ipv4=True,
        supports_ipv6=False,
        requires_multiple_requests=True,
    )
    db_session.add(test_domain_fail)

    # Add test relay
    test_relay = Relay(
        fingerprint="A53C46F5B157DD83366D45A8E99A244934A14C46",
        ipv4_address="128.31.0.13",
        ipv4_exiting_allowed=True,
        ipv6_exiting_allowed=False,
    )
    db_session.add(test_relay)

    # Add test fetchers
    test_fetcher_non_tor = Fetcher(method="firefox_browser", version="82")
    db_session.add(test_fetcher_non_tor)

    test_fetcher_tor = Fetcher(
        method="firefox_browser", uses_proxy_type="tor", version="82"
    )
    db_session.add(test_fetcher_tor)

    # Commit changes to the database
    db_session.commit()


@pytest.mark.usefixtures("insert_relay_and_domain")
class TestWorker:
    @staticmethod
    def test_worker_single_run_without_tor_success(config, db_session):
        worker = Worker(
            worker_id="0",
            config=config,
            db_session=db_session,
            loop=False,
        )

        # Insert a job
        new_job = FetchQueue(
            url="https://check.torproject.org",
            fetcher_id=1,
            domain_id=1,
            relay_id=1,
        )
        db_session.add(new_job)

        # Commit changes to the database
        db_session.commit()

        # Check successful jobs
        db_job = db_session.query(FetchCompleted)
        assert db_job.count() == 0

        # Process the job
        worker.process_next_job()

        assert db_job.count() != 0
        assert db_job.first().url == "https://check.torproject.org"

    @staticmethod
    def test_worker_single_run_without_tor_fail(config, db_session):
        worker = Worker(
            worker_id="0",
            config=config,
            db_session=db_session,
            loop=False,
        )

        # Insert a job
        new_job = FetchQueue(
            url="https://stupid.urlextension",
            fetcher_id=1,
            domain_id=2,
            relay_id=1,
        )
        db_session.add(new_job)

        # Commit changes to the database
        db_session.commit()

        # Check failed jobs
        db_job = db_session.query(FetchFailed)
        assert db_job.count() == 0

        # Process the job
        worker.process_next_job()

        assert db_job.count() != 0
        assert db_job.first().url == "https://stupid.urlextension"

    @staticmethod
    def test_worker_single_run_with_tor_success(config, db_session):
        worker = Worker(
            worker_id="0",
            config=config,
            db_session=db_session,
            loop=False,
        )

        # Insert a job
        new_job = FetchQueue(
            url="https://check.torproject.org",
            fetcher_id=2,
            domain_id=1,
            relay_id=1,
        )
        db_session.add(new_job)

        # Commit changes to the database
        db_session.commit()

        # Check successful jobs
        db_job = db_session.query(FetchCompleted)
        assert db_job.count() == 0

        # Process the job
        worker.process_next_job()

        assert db_job.count() != 0
        assert db_job.first().url == "https://check.torproject.org"

    @staticmethod
    def test_worker_single_run_with_tor_fail(config, db_session):
        worker = Worker(
            worker_id="0",
            config=config,
            db_session=db_session,
            loop=False,
        )

        # Insert a job
        new_job = FetchQueue(
            url="https://stupid.urlextension",
            fetcher_id=2,
            domain_id=2,
            relay_id=1,
        )
        db_session.add(new_job)

        # Commit changes to the database
        db_session.commit()

        # Check failed jobs
        db_job = db_session.query(FetchFailed)
        assert db_job.count() == 0

        # Process the job
        worker.process_next_job()

        assert db_job.count() != 0
        assert db_job.first().url == "https://stupid.urlextension"

    @staticmethod
    def test_worker_no_job_in_queue(config, db_session):
        worker = Worker(
            worker_id="0",
            config=config,
            db_session=db_session,
            loop=False,
        )

        # Process the job, shouldn't rise any errors
        worker.process_next_job()
