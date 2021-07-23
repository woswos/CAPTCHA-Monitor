# pylint: disable=C0115,C0116,W0212

import pytest

from captchamonitor.core.worker import Worker
from captchamonitor.utils.models import FetchQueue, FetchCompleted, AnalyzeCompleted
from captchamonitor.core.analyzer import Analyzer


@pytest.fixture()
def insert_and_process_jobs(
    config, db_session, firefox_id, firefox_http_proxy_id, tor_browser_id
):
    test_url = "https://api.ipify.org"

    worker = Worker(
        worker_id="0",
        config=config,
        db_session=db_session,
        loop=False,
    )

    db_session.add(
        FetchQueue(
            url=test_url,
            fetcher_id=firefox_id,
            domain_id=1,
        )
    )

    db_session.add(
        FetchQueue(
            url=test_url,
            fetcher_id=tor_browser_id,
            domain_id=1,
            relay_id=1,
        )
    )

    db_session.add(
        FetchQueue(
            url=test_url,
            fetcher_id=firefox_http_proxy_id,
            domain_id=1,
            proxy_id=1,
        )
    )

    db_session.add(
        FetchQueue(
            url=test_url,
            fetcher_id=firefox_http_proxy_id,
            domain_id=1,
            proxy_id=2,
        )
    )

    db_session.commit()

    # Check if the FetchCompleted table is empty
    assert db_session.query(FetchCompleted).count() == 0

    # Process the jobs
    for _ in range(4):
        worker.process_next_job()

    # Make sure that the jobs are processed
    assert db_session.query(FetchCompleted).count() == 4


@pytest.mark.usefixtures(
    "insert_domains_fetchers_relays_proxies", "insert_and_process_jobs"
)
class TestAnalyzer:
    @staticmethod
    def test_analyzer_init(config, db_session):
        # Since the analyze completed hasn't been called yet so the table is empty as of now
        assert db_session.query(AnalyzeCompleted).count() == 0

        Analyzer(
            analyzer_id="0",
            config=config,
            db_session=db_session,
            loop=False,
        ).process_next_batch_of_domains()

        assert db_session.query(AnalyzeCompleted).count() == 1

        # Resembles Same or Equal Resemblance
        assert (
            db_session.query(AnalyzeCompleted).first().dom_analyze == 4
            or db_session.query(AnalyzeCompleted).first().dom_analyze == 1
        )

        # No Captcha
        assert db_session.query(AnalyzeCompleted).first().captcha_checker == 0

        # Status Code Same
        assert db_session.query(AnalyzeCompleted).first().status_check is None

        # Consensus Lite Dom is not executed as site isn't suspicious
        assert db_session.query(AnalyzeCompleted).first().consensus_lite_dom is None

        # Consensus Lite Captcha is not executed as site isn't suspicious
        assert db_session.query(AnalyzeCompleted).first().consensus_lite_captcha is None
