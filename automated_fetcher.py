#!/usr/bin/env python

"""
Check if a web site returns a CloudFlare CAPTCHA using Tor Browser and httplib
"""

import time
import sys
import csv
import itertools
import os.path

import cloudflared_tor as cf_tor
import cloudflared_httplib as cf_httplib


def main():
    # Create the output file if doesn't exists
    fields = {'time_stamp', 'method', 'url', 'result', 'captcha_sign', 'tbb_path'}
    output_file = 'results.csv'
    check_if_csv_exists(output_file, fields)

    # The parameters required to run the tests
    params = {}
    params['captcha_sign'] = 'Attention Required! | Cloudflare'
    params['tbb_path'] = '/home/woswos/tor-browser_en-US'

    params['url'] = 'http://captcha.wtf/complex.html'

    result = cf_httplib.is_cloudflared(params)
    append_to_csv(output_file, result)


def check_if_csv_exists(output_file, fields):
    if not os.path.isfile(output_file):
        with open(output_file, 'w+') as file:
            w = csv.DictWriter(file, fields)
            w.writeheader()


def append_to_csv(output_file, data):
    with open(output_file, 'a') as f:
        w = csv.DictWriter(f, data.keys())
        w.writerow(data)


if __name__ == '__main__':
    main()
    sys.exit(0)
