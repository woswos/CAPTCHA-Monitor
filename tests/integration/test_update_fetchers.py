import unittest

from captchamonitor.utils.config import Config
from captchamonitor.utils.models import Fetcher
from captchamonitor.utils.database import Database
from captchamonitor.core.update_fetchers import UpdateFetchers


class TestUpdateFetchers(unittest.TestCase):
    def setUp(self):
        self.config = Config()
        self.database = Database(
            self.config["db_host"],
            self.config["db_port"],
            self.config["db_name"],
            self.config["db_user"],
            self.config["db_password"],
        )
        self.db_session = self.database.session()
        self.db_fetcher_query = self.db_session.query(Fetcher)

    def tearDown(self):
        self.db_session.close()

    def test_discover_browser_containers(self):
        update_fetchers = UpdateFetchers(config=self.config, db_session=self.db_session)

        browsers = update_fetchers._UpdateFetchers__discover_browser_containers()

        self.assertGreater(len(browsers), 0)
        self.assertIn("tor_browser", browsers)

    def test_update_fetchers(self):
        # Make sure the table is empty
        self.assertEqual(self.db_fetcher_query.count(), 0)

        update_fetchers = UpdateFetchers(config=self.config, db_session=self.db_session)

        # Check if fetchers were inserted
        self.assertNotEqual(self.db_fetcher_query.count(), 0)

        self.assertNotEqual(
            self.db_fetcher_query.filter(Fetcher.method == "tor_browser").count(),
            0,
        )
