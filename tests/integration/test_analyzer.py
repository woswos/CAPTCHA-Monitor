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
from captchamonitor.utils.small_scripts import get_random_http_proxy


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

    country = "US"
    # The try catch was added because of two things:
    # 1. I was receiving JSONDecodeError (https://github.com/simplejson/simplejson/blob/v3.0.5/simplejson/decoder.py#L33)
    # 2. The pubproxy.com has a limit of 50 requests per day
    try:
        host = (get_random_http_proxy(country)[0],)
        port = (get_random_http_proxy(country)[1],)
    except ValueError:
        host = ("45.42.177.7",)
        port = (3128,)

    proxy1 = Proxy(
        host=host,
        port=port,
        country=country,
        google_pass=False,
        anonymity="N",
        incoming_ip_different_from_outgoing_ip=False,
        ssl=True,
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
    test_fetcher_proxy = Fetcher(
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
        fetcher_id=3,
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
    db_session.add(test_fetcher_proxy)
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
    assert db_session.query(AnalyzeCompleted).count() == 2


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

        # No Captcha
        assert db_session.query(AnalyzeCompleted).first().captcha_checker == 0

        # Status Code Same
        assert db_session.query(AnalyzeCompleted).first().status_check is None
