# pylint: disable=C0115,C0116,W0212

import pytest

from captchamonitor.utils.models import FetchQueue
from captchamonitor.core.schedule_jobs import ScheduleJobs


@pytest.mark.usefixtures("insert_domains_fetchers_relays_proxies")
class TestScheduleJobs:
    @staticmethod
    def test_schedule_jobs_init(config, db_session):
        schedule_jobs = ScheduleJobs(
            config=config,
            db_session=db_session,
            loop=False,
        )

        # Check if the queue is empty
        assert db_session.query(FetchQueue).count() == 0

        # Schedule jobs
        schedule_jobs.schedule_next_batch()

        # Check if jobs are scheduled
        assert db_session.query(FetchQueue).count() > 5
