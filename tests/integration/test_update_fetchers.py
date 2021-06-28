from captchamonitor.utils.models import Fetcher
from captchamonitor.core.update_fetchers import UpdateFetchers


class TestUpdateFetchers:
    def test_discover_browser_containers(self, config, db_session):
        update_fetchers = UpdateFetchers(config=config, db_session=db_session)

        browsers = update_fetchers._UpdateFetchers__discover_browser_containers()

        assert len(browsers) > 0
        assert "tor_browser" in browsers

    def test_update_fetchers(self, config, db_session):
        db_fetcher_query = db_session.query(Fetcher)

        # Make sure the table is empty
        assert db_fetcher_query.count() == 0

        update_fetchers = UpdateFetchers(config=config, db_session=db_session)

        # Check if fetchers were inserted
        assert db_fetcher_query.count() != 0

        assert db_fetcher_query.filter(Fetcher.method == "tor_browser").count() != 0
