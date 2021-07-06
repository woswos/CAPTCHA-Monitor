# pylint: disable=C0115,C0116,W0212

import pytest

from captchamonitor.core.worker import Worker
from captchamonitor.utils.models import (
    Proxy,
    Relay,
    Domain,
    Fetcher,
    FetchQueue,
    FetchCompleted,
    AnalyzeCompleted,
)
from captchamonitor.core.analyzer import Analyzer
from captchamonitor.fetchers.base_fetcher import BaseFetcher
from captchamonitor.fetchers.firefox_browser import FirefoxBrowser


@pytest.fixture()
def insert_and_process_jobs(config, db_session):
    test_domain = "api.ipify.org"

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

    proxy1 = Proxy(
        host="81.91.137.43",
        port=8080,
        country="IR",
        google_pass=True,
        anonymity="N",
        incoming_ip_different_from_outgoing_ip=False,
        ssl=False,
    )

    proxy2 = Proxy(
        host="96.95.164.41",
        port=3128,
        country="US",
        google_pass=True,
        anonymity="N",
        incoming_ip_different_from_outgoing_ip=False,
        ssl=False,
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
    test_fetcher_proxy1 = Fetcher(
        method="firefox_browser",
        uses_proxy_type="http",
        version="82",
    )
    test_fetcher_proxy2 = Fetcher(
        method="firefox_browser",
        uses_proxy_type="http",
        version="82",
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

    queue_proxy1 = FetchQueue(
        url=f"https://{test_domain}",
        fetcher_id=3,
        domain_id=1,
        proxy_id=1,
    )

    queue_proxy2 = FetchQueue(
        url=f"https://{test_domain}",
        fetcher_id=4,
        domain_id=1,
        proxy_id=2,
    )
    # Commit changes to the database
    db_session.add(domain)
    db_session.add(proxy1)
    db_session.add(proxy2)
    db_session.add(test_relay)
    db_session.add(test_fetcher_non_tor)
    db_session.add(test_fetcher_tor)
    db_session.add(test_fetcher_proxy1)
    db_session.add(test_fetcher_proxy2)
    db_session.add(queue_non_tor)
    db_session.add(queue_tor)
    db_session.add(queue_proxy1)
    db_session.add(queue_proxy2)
    db_session.commit()

    # Check if the FetchCompleted table is empty
    assert db_session.query(FetchCompleted).count() == 0

    # Process the non tor job
    worker.process_next_job()

    # Process the tor job
    worker.process_next_job()

    # Process the first proxy job
    worker.process_next_job()

    # Process the second proxy job
    worker.process_next_job()

    # Make sure that the jobs are processed
    assert db_session.query(FetchCompleted).count() == 4
    # Since the analyze completed hasn't been called yet so the table is empty as of now
    assert db_session.query(AnalyzeCompleted).count() == 0


@pytest.mark.usefixtures("insert_and_process_jobs")
class TestAnalyzer:
    @staticmethod
    def test_analyzer_init(config, db_session):
        Analyzer(
            analyzer_id="0",
            config=config,
            db_session=db_session,
            loop=False,
        ).process_next_batch_of_domains()

        assert db_session.query(AnalyzeCompleted).count() == 2

        # Resembles Same or Similar Resemblance
        assert (
            db_session.query(AnalyzeCompleted).first().dom_analyze == 4
            or db_session.query(AnalyzeCompleted).first().dom_analyze == 1
        )

        # # No Captcha
        assert db_session.query(AnalyzeCompleted).first().captcha_checker == 0

        # Status Code Same
        assert db_session.query(AnalyzeCompleted).first().status_check is None
