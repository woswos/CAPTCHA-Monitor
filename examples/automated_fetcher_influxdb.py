#!/usr/bin/env python2

"""
Check if a web site returns a CloudFlare CAPTCHA using Tor Browser & httplib
and submit results to an InfluxDB database
"""

import cloudflared_httplib as cf_httplib
import cloudflared_tor as cf_tor
import time
import sys
import csv
import itertools
import os.path
import json
from influxdb import InfluxDBClient
import logging

sys.path.append("../CAPTCHA-Monitor")

logger_format = '%(asctime)s :: %(module)s :: %(levelname)s :: %(message)s'
logging.basicConfig(format=logger_format)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


host = 'localhost'
port = 8086
user_name = ''
password = ''
db = 'captcha'


def main():
    url_list = ['http://captcha.wtf',
                'https://captcha.wtf',
                'http://captcha.wtf/complex.html',
                'https://captcha.wtf/complex.html',
                'http://bypass.captcha.wtf',
                'https://bypass.captcha.wtf',
                'http://bypass.captcha.wtf/complex.html',
                'https://bypass.captcha.wtf/complex.html',
                'http://exit11.online',
                'https://exit11.online',
                'http://exit11.online/complex.html',
                'https://exit11.online/complex.html',
                'http://bypass.exit11.online',
                'https://bypass.exit11.online',
                'http://bypass.exit11.online/complex.html',
                'https://bypass.exit11.online/complex.html']

    # The parameters required to run the tests
    params = {}
    results = {}
    params['captcha_sign'] = 'Cloudflare'
    params['tbb_path'] = '/home/woswos/tor-browser_en-US'
    params['headless_mode'] = False  # make this True if running on a non-GUI OS

    # Iterate over the url list
    for i, url in enumerate(url_list):
        params['url'] = url

        # Test with httplib
        test_with(cf_httplib, params)

        # Test with Tor
        test_with(cf_tor, params)

    logger.info('Completed testing')


# Perform a test with the given paramters and send results to DB
def test_with(method, params):
    results = method.is_cloudflared(params)
    logger.info('Test result for %s with %s is %s' %
                (results.get('url'), results.get('method'), results.get('result')))
    submit_to_influxdb(results)


# Submits given results to InfluxDB database
def submit_to_influxdb(data):
    # Set database connection
    client = InfluxDBClient(host, port, user_name, password, db)

    # Prepare the json payload in the InfluxDB format
    influxdb_json = [
        {
            'measurement': data['method'],
            'tags': {
                'url': data['url'],
                'captcha_sign': data['captcha_sign'],
                'headless_mode': data['headless_mode']
            },
            # 'time': data['time_stamp'],
            'fields': {
                'result': data['result']
            }
        }
    ]

    logger.debug(influxdb_json)

    # Try to connect to the database
    try:
        client.write_points(influxdb_json)

    except Exception as err:
        logger.critical(
            'Double check the connection credentials because InfluxDBClient() says: %s' % err)


if __name__ == '__main__':
    main()
    sys.exit(0)
