from captchamonitor.utils.models import Proxy
from captchamonitor.core.update_proxy import UpdateProxy
from captchamonitor.utils.proxy_parser import ProxyParser


class TestUpdateProxy:
    def test__insert_proxies_into_db(self, config, db_session):
        db_proxy_query = db_session.query(Proxy)

        update_proxy = UpdateProxy(
            config=config, db_session=db_session, auto_update=False
        )

        # Get proxy data
        proxy_list = ProxyParser()
        proxy_list.get_proxy_details()
        proxy_anon_example = proxy_list.proxy_anon
        proxy_host_example = proxy_list.proxy_host
        proxy_port_example = proxy_list.proxy_port
        proxy_ssl_example = proxy_list.proxy_ssl
        proxy_google_pass_example = proxy_list.proxy_google_pass
        proxy_country_example = proxy_list.proxy_country
        proxy_incoming_ip_example = proxy_list.incoming_ip_different_from_outgoing_ip

        # Check if the url table is empty
        assert db_proxy_query.count() == 0

        update_proxy._UpdateProxy__insert_proxy_into_db(
            proxy_host_list=proxy_host_example,
            proxy_port_list=proxy_port_example,
            proxy_ssl_list=proxy_ssl_example,
            proxy_google_pass_list=proxy_google_pass_example,
            proxy_country_list=proxy_country_example,
            proxy_anon_list=proxy_anon_example,
            proxy_incoming_ip_different_from_outgoing_ip_list=proxy_incoming_ip_example,
        )
        # Check if the proxy table was populated with correct data
        assert db_proxy_query.count() == len(proxy_anon_example)
        assert proxy_host_example[0] == db_proxy_query.first().proxy_host
