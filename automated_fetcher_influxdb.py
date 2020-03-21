#!/usr/bin/env python

"""
Check if a web site returns a CloudFlare CAPTCHA using Tor Browser & httplib
and submit results to an InfluxDB database
"""

import time
import sys
import csv
import itertools
import os.path
import json
from influxdb import InfluxDBClient

import cloudflared_tor as cf_tor
import cloudflared_httplib as cf_httplib

host = 'localhost'
port = 8086
user_name = ''
password = ''
db = 'db_name'


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
    params['captcha_sign'] = 'Attention Required! | Cloudflare'
    params['tbb_path'] = '/home/woswos/tor-browser_en-US'
    params['headless_mode'] = False # make this True if running on a non-GUI OS

    # Iterate over the url list
    for i, url in enumerate(url_list):
        print('Testing %s' % url)
        params['url'] = url

        # Test with httplib
        results = cf_httplib.is_cloudflared(params)
        submit_to_influxdb(results)

        # Test with Tor
        results = cf_tor.is_cloudflared(params)
        submit_to_influxdb(results)


# Submits given results to InfluxDB database
def submit_to_influxdb(data):
    # Connect to the database
    client = InfluxDBClient(host, port, user_name, password, db)

    # Prepare the json payload in the InfluxDB format
    influxdb_json = [
        {
            'measurement': data['method'],
            'tags': {
                'url': data['url'],
                'captcha_sign': data['captcha_sign']
            },
            'time': data['time_stamp'],
            'fields': {
                'result': data['result']
            }
        }
    ]

    client.write_points(influxdb_json)


if __name__ == '__main__':
    main()
    sys.exit(0)
