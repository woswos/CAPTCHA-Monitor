# pylint: disable=C0115,C0116,W0212

import pytest

from captchamonitor.core.worker import Worker
from captchamonitor.utils.models import FetchQueue, FetchFailed, FetchCompleted


@pytest.mark.usefixtures("insert_domains_fetchers_relays_proxies")
class TestWorker:
    @staticmethod
    def test_worker_single_run_without_tor_success(config, db_session, firefox_id):
        worker = Worker(
            worker_id="0",
            config=config,
            db_session=db_session,
            loop=False,
        )

        # Insert a job
        db_session.add(
            FetchQueue(
                url="https://check.torproject.org",
                fetcher_id=firefox_id,
                domain_id=1,
                relay_id=1,
            )
        )

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
    def test_worker_single_run_without_tor_fail(config, db_session, firefox_id):
        worker = Worker(
            worker_id="0",
            config=config,
            db_session=db_session,
            loop=False,
        )

        # Insert a job
        db_session.add(
            FetchQueue(
                url="https://stupid.urlextension",
                fetcher_id=firefox_id,
                domain_id=2,
                relay_id=1,
            )
        )

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
    def test_worker_single_run_with_tor_success(
        config, db_session, firefox_tor_proxy_id
    ):
        worker = Worker(
            worker_id="0",
            config=config,
            db_session=db_session,
            loop=False,
        )

        # Insert a job
        db_session.add(
            FetchQueue(
                url="https://check.torproject.org",
                fetcher_id=firefox_tor_proxy_id,
                domain_id=1,
                relay_id=1,
            )
        )

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
    def test_worker_single_run_with_tor_fail(config, db_session, firefox_tor_proxy_id):
        worker = Worker(
            worker_id="0",
            config=config,
            db_session=db_session,
            loop=False,
        )

        # Insert a job
        db_session.add(
            FetchQueue(
                url="https://stupid.urlextension",
                fetcher_id=firefox_tor_proxy_id,
                domain_id=2,
                relay_id=1,
            )
        )

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
