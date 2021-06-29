import pytest

from captchamonitor.utils.models import Relay, Domain, Fetcher, FetchQueue
from captchamonitor.core.schedule_jobs import ScheduleJobs


@pytest.fixture()
def insert_jobs_and_fetchers(db_session):
    assert db_session.query(FetchQueue).count() == 0

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

    test_fetcher_non_tor = Fetcher(method="firefox_browser", version="82")

    test_fetcher_tor = Fetcher(
        method="tor_browser", uses_proxy_type="tor", version="82"
    )

    # Commit changes to the database
    db_session.add(domain_1)
    db_session.add(domain_2)
    db_session.add(test_relay)
    db_session.add(test_fetcher_non_tor)
    db_session.add(test_fetcher_tor)
    db_session.commit()


@pytest.mark.usefixtures("insert_jobs_and_fetchers")
class TestScheduleJobs:
    def test_schedule_jobs_init(self, config, db_session):
        schedule_jobs = ScheduleJobs(
            config=config,
            db_session=db_session,
            loop=False,
        )

        # Schedule jobs
        schedule_jobs.schedule_next_batch()

        # Check if jobs are scheduled
        assert db_session.query(FetchQueue).count() == 4
