from captchamonitor.utils.models import Proxy
from captchamonitor.core.update_proxy import UpdateProxy
from captchamonitor.utils.proxy_parser import ProxyParser


class TestUpdateProxy:
    def test__insert_similar_proxies_into_db(self, config, db_session):
        # Check for similar proxy but not identical
        db_proxy_query = db_session.query(Proxy)
        update_proxy = UpdateProxy(
            config=config, db_session=db_session, auto_update=False
        )
        # Check if the proxy table is empty
        assert db_proxy_query.count() == 0

        update_proxy._UpdateProxy__insert_proxy_into_db(
            host_list=["127.0.0.1", "127.0.0.1"],
            port_list=["8080", "80"],
            ssl_list=[True, True],
            google_pass_list=[True, False],
            country_list=["XY", "XY"],
            anonymity_list=["A", "N"],
            incoming_ip_different_from_outgoing_ip_list=[True, False],
        )

        assert db_proxy_query.count() == 2

    def test__insert_proxies_into_db(self, config, db_session):
        db_proxy_query = db_session.query(Proxy)

        update_proxy = UpdateProxy(
            config=config, db_session=db_session, auto_update=False
        )

        # Get proxy data
        proxy_list = ProxyParser()
        proxy_list.get_proxy_details_spys()

        # Check if the proxy table is empty
        assert db_proxy_query.count() == 0

        update_proxy._UpdateProxy__insert_proxy_into_db(
            host_list=proxy_list.host,
            port_list=proxy_list.port,
            ssl_list=proxy_list.ssl,
            google_pass_list=proxy_list.google_pass,
            country_list=proxy_list.country,
            anonymity_list=proxy_list.anonymity,
            incoming_ip_different_from_outgoing_ip_list=proxy_list.incoming_ip_different_from_outgoing_ip,
        )

        # Check if the proxy table was populated with correct number of data
        assert db_proxy_query.count() == len(proxy_list.host)
        # Check if the proxy table was populated with the correct data, checking for host
        assert proxy_list.host[0] == db_proxy_query.first().host
        # Check if the proxy table was populated with the correct data, checking for port
        assert proxy_list.port[0] == db_proxy_query.first().port
        # Check if the proxy table was populated with the correct data, checking for ssl
        assert proxy_list.ssl[0] == db_proxy_query.first().ssl
        # Check if the proxy table was populated with the correct data, checking for google passer
        assert proxy_list.google_pass[0] == db_proxy_query.first().google_pass
        # Check if the proxy table was populated with the correct data, checking for country code
        assert proxy_list.country[0] == db_proxy_query.first().country
        # Check if the proxy table was populated with the correct data, checking for anonymity
        assert proxy_list.anonymity[0] == db_proxy_query.first().anonymity
        # Check if the proxy table was populated with the correct data, checking for incoming ip different from outgoing ip
        assert (
            proxy_list.incoming_ip_different_from_outgoing_ip[0]
            == db_proxy_query.first().incoming_ip_different_from_outgoing_ip
        )
