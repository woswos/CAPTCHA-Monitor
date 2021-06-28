from captchamonitor.utils.models import Domain
from captchamonitor.core.update_domains import UpdateDomains
from captchamonitor.utils.website_parser import WebsiteParser


class TestUpdateDomains:
    def test__insert_alexa_website_into_db(self, config, db_session):
        db_website_query = db_session.query(Domain)

        update_domains = UpdateDomains(
            config=config, db_session=db_session, auto_update=False
        )

        # Get website data
        website_list = WebsiteParser()
        website_list.get_alexa_top_50()
        website_data = website_list.website_list[:2]

        # Check if the url table is empty
        assert db_website_query.count() == 0

        update_domains._UpdateDomains__insert_website_into_db(website_data)

        # Check if the url table was populated with correct data
        assert db_website_query.count() == len(website_data)
        assert website_data[0] == db_website_query.first().domain

    def test__insert_moz_website_into_db(self, config, db_session):
        db_website_query = db_session.query(Domain)

        update_domains = UpdateDomains(
            config=config, db_session=db_session, auto_update=False
        )

        # Get website data
        website_list = WebsiteParser()
        website_list.get_moz_top_500()
        website_data = website_list.website_list[:2]

        # Check if the url table is empty
        assert db_website_query.count() == 0

        update_domains._UpdateDomains__insert_website_into_db(website_data)

        # Check if the url table was populated with correct data
        assert db_website_query.count() == len(website_data)
        assert website_data[0] == db_website_query.first().domain

    def test_update_url_init_with_already_populated_table(self, config, db_session):
        db_website_query = db_session.query(Domain)

        # Prepopulate the table
        update_domains = UpdateDomains(
            config=config, db_session=db_session, auto_update=False
        )
        # Check if the url table is empty
        assert db_website_query.count() == 0

        # Get website data
        website_list = WebsiteParser()
        website_list.get_alexa_top_50()
        website_data = website_list.website_list[:2]

        update_domains._UpdateDomains__insert_website_into_db(website_data)

        # Check if the url table was populated with correct data
        assert db_website_query.count() == len(website_data)
        assert db_website_query.first().domain == website_data[0]

        # Try inserting the same url again with different details
        update_domains._UpdateDomains__insert_website_into_db(website_data)

        # Make sure there still only one url
        assert db_website_query.count() == len(website_data)
        assert db_website_query.first().domain == website_data[0]
