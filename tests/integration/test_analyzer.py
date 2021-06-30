import pytest

from captchamonitor.core.worker import Worker
from captchamonitor.utils.models import (
    Relay,
    Domain,
    Fetcher,
    FetchQueue,
    FetchCompleted,
    AnalyzeCompleted,
)
from captchamonitor.core.analyzer import Analyzer


@pytest.fixture()
def insert_and_process_jobs(config, db_session):
    test_domain = "duckduckgo.com"

    worker = Worker(
        worker_id="0",
        config=config,
        db_session=db_session,
        loop=False,
    )

    domain = Domain(
        domain=test_domain,
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

    test_fetcher_non_tor = Fetcher(method="firefox_browser", version="82")

    test_fetcher_tor = Fetcher(
        method="tor_browser", uses_proxy_type="tor", version="82"
    )

    queue_non_tor = FetchQueue(
        url=f"https://{test_domain}",
        fetcher_id=1,
        domain_id=1,
    )

    queue_tor = FetchQueue(
        url=f"https://{test_domain}",
        fetcher_id=2,
        domain_id=1,
        relay_id=1,
    )

    # Commit changes to the database
    db_session.add(domain)
    db_session.add(test_relay)
    db_session.add(test_fetcher_non_tor)
    db_session.add(test_fetcher_tor)
    db_session.add(queue_non_tor)
    db_session.add(queue_tor)
    db_session.commit()

    # Process the non tor job
    worker.process_next_job()

    # Process the tor job
    worker.process_next_job()

    # Make sure that the jobs are processed
    assert db_session.query(FetchCompleted).count() == 2
    assert db_session.query(AnalyzeCompleted).count() == 0


@pytest.mark.usefixtures("insert_and_process_jobs")
class TestAnalyzer:
    def test_analyzer_init(self, config, db_session):
        Analyzer(
            analyzer_id="0",
            config=config,
            db_session=db_session,
            loop=False,
        ).process_next_batch_of_domains()

        # Resembles Same
        assert db_session.query(AnalyzeCompleted).first().dom_analyze == 1

        # No Captcha
        assert db_session.query(AnalyzeCompleted).first().captcha_checker == 0

        # Status Code Same
        assert db_session.query(AnalyzeCompleted).first().status_check == None
