import unittest
from datetime import datetime

import pytest
from freezegun import freeze_time

from captchamonitor.utils.config import Config
from captchamonitor.utils.models import Domain
from captchamonitor.utils.database import Database
from captchamonitor.core.update_domains import UpdateDomains
from captchamonitor.utils.website_parser import WebsiteParser


class TestUpdateDomains(unittest.TestCase):
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
        self.db_website_query = self.db_session.query(Domain)
        self.alexa_url_count = 50
        self.moz_url_count = 500

    def tearDown(self):
        self.db_session.close()

    def test__insert_alexa_website_into_db(self):
        update_domains = UpdateDomains(
            config=self.config, db_session=self.db_session, auto_update=False
        )

        # Get website data
        website_list = WebsiteParser()
        website_list.get_alexa_top_50()
        website_data = website_list.website_list

        # Check if the url table is empty
        self.assertEqual(self.db_website_query.count(), 0)

        update_domains._UpdateDomains__insert_website_into_db(website_data)

        # Check if the url table was populated with correct data
        self.assertEqual(self.db_website_query.count(), self.alexa_url_count)
        self.assertEqual(website_data[0], self.db_website_query.first().domain)

    def test__insert_moz_website_into_db(self):
        update_domains = UpdateDomains(
            config=self.config, db_session=self.db_session, auto_update=False
        )

        # Get website data
        website_list = WebsiteParser()
        website_list.get_moz_top_500()
        website_data = website_list.website_list

        # Check if the url table is empty
        self.assertEqual(self.db_website_query.count(), 0)

        update_domains._UpdateDomains__insert_website_into_db(website_data)

        # Check if the url table was populated with correct data
        self.assertEqual(self.db_website_query.count(), self.moz_url_count)
        self.assertEqual(website_data[0], self.db_website_query.first().domain)

    def test_update_url_init_with_already_populated_table(self):
        # Prepopulate the table
        update_domains = UpdateDomains(
            config=self.config, db_session=self.db_session, auto_update=False
        )
        # Check if the url table is empty
        self.assertEqual(self.db_website_query.count(), 0)

        # Get website data
        website_list = WebsiteParser()
        website_list.get_alexa_top_50()
        website_data = website_list.website_list

        update_domains._UpdateDomains__insert_website_into_db(website_data)

        # Check if the url table was populated with correct data
        self.assertEqual(self.db_website_query.count(), self.alexa_url_count)
        self.assertEqual(self.db_website_query.first().domain, website_data[0])

        # Try inserting the same url again with different details
        update_domains._UpdateDomains__insert_website_into_db(website_data)

        # Make sure there still only one url
        self.assertEqual(self.db_website_query.count(), self.alexa_url_count)
        self.assertEqual(self.db_website_query.first().domain, website_data[0])

        # Add lists from moz website on top of alexa websites
        website_list.get_moz_top_500()
        website_data = website_list.website_list
        # Unique length of website
        unique_length_of_website = len(website_list.unique_website_list)

        update_domains._UpdateDomains__insert_website_into_db(website_data)

        # Check if the count of url table is equal to the length of unique websites
        self.assertEqual(self.db_website_query.count(), unique_length_of_website)
