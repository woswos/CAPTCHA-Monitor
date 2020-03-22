#!/usr/bin/env python2

"""
Check if a web site returns a CloudFlare CAPTCHA using Tor Browser and httplib
"""

import time
import sys
import csv
import itertools
import os.path
import logging

sys.path.append("..")
import cloudflared_tor as cf_tor
import cloudflared_httplib as cf_httplib

logger_format = '%(asctime)s :: %(module)s :: %(levelname)s :: %(message)s'
logging.basicConfig(format=logger_format)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def main():
    output_file = 'results.csv'

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
        params['url'] = url

        # Test with httplib
        test_with(cf_httplib, params, output_file)

        # Test with Tor
        test_with(cf_tor, params, output_file)

    logger.info('Completed testing')


# Perform a test with the given paramters and append result to the CSV file
def test_with(method, params, output_file):
    results = method.is_cloudflared(params)
    logger.info('Test result for %s with %s is %s' % (results.get('url'), results.get('method'), results.get('result')))
    append_to_csv(output_file, results)


# Appends the passed result to the CSV file
def append_to_csv(output_file, data):
    # Create the output file if it doesn't exists
    # Insert the header
    if not os.path.isfile(output_file):
        with open(output_file, 'w+') as file:
            writer = csv.DictWriter(file, data.keys())
            writer.writeheader()

    # Append to file
    with open(output_file, 'a') as file:
        writer = csv.DictWriter(file, data.keys())
        writer.writerow(data)


if __name__ == '__main__':
    main()
    sys.exit(0)
