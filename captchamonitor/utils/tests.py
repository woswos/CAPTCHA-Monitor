import logging
import os
import json
from captchamonitor.utils.sqlite import SQLite


class Tests:
    def __init__(self):
        """
        This class is used for interacting with the 'urls' and 'fetchers' table in the database
        """
        self.db = SQLite()
        self.db.check_if_db_exists()
        self.logger = logging.getLogger(__name__)

    def get_urls(self, ipv4_only=False, ipv6_only=False):
        urls = self.db.get_table_entries(self.db.urls_table_name)

        if not urls:
            return None

        ipv4_urls = []
        ipv6_urls = []
        for url in urls:
            temp = {}
            temp['url'] = url['url']
            temp['hash'] = url['hash']

            if url['supports_ipv6'] == '1':
                ipv6_urls.append(temp)

            if url['supports_ipv4'] == '1':
                ipv4_urls.append(temp)

        if ipv6_only:
            return ipv6_urls
        elif ipv4_only:
            return ipv4_urls
        else:
            return ipv6_urls + ipv4_urls

    def get_fetchers(self):
        fetchers = self.db.get_table_entries(self.db.fetchers_table_name)

        if not fetchers:
            return None

        methods = []
        for fetcher in fetchers:
            temp = {}
            temp['method'] = fetcher['method']
            temp['versions'] = json.loads(fetcher['versions'])['data']

            if fetcher['option_1']:
                temp['option_1'] = json.loads(fetcher['option_1'])['data']

            if fetcher['option_2']:
                temp['option_2'] = json.loads(fetcher['option_2'])['data']

            if fetcher['option_2']:
                temp['option_2'] = json.loads(fetcher['option_2'])['data']

            methods.append(temp)

        return methods
