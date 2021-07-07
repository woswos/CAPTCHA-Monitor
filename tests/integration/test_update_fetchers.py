# pylint: disable=C0115,C0116,W0212

from captchamonitor.utils.models import Fetcher
from captchamonitor.core.update_fetchers import UpdateFetchers


class TestUpdateFetchers:
    @staticmethod
    def test_discover_browser_containers(config, db_session):
        update_fetchers = UpdateFetchers(config=config, db_session=db_session)

        browsers = update_fetchers._UpdateFetchers__discover_browser_containers()

        assert len(browsers) > 0
        assert "tor_browser" in browsers

    @staticmethod
    def test_update_fetchers(config, db_session):
        db_fetcher_query = db_session.query(Fetcher)

        # Make sure the table is empty
        assert db_fetcher_query.count() == 0

        UpdateFetchers(config=config, db_session=db_session)

        # Check if fetchers were inserted
        assert db_fetcher_query.count() != 0

        assert db_fetcher_query.filter(Fetcher.method == "tor_browser").count() != 0
