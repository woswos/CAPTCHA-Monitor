#!/usr/bin/env python

"""
Check if a web site returns a CloudFlare CAPTCHA using selenium and Tor browser

Used library: https://github.com/webfp/tor-browser-selenium
"""

from argparse import ArgumentParser
from tbselenium.tbdriver import TorBrowserDriver
from selenium.webdriver.support.ui import Select
import sys
import time


def main():
    # ArgumentParser details
    desc = """Check if a web site returns a CloudFlare CAPTCHA using tor
    browser. By default, this tool is looking for the
    'Attention Required! | Cloudflare' text within the fetched web site.
    """
    parser = ArgumentParser(description=desc)
    parser.add_argument('-u', metavar='url', help='destination url',
        required=True)
    parser.add_argument('-t', metavar='tor_browser_path',
        help='path to Tor browser bundle',
        required=True)
    parser.add_argument('-c', metavar='captcha',
        help='the captcha sign expected to see in the page (default: "Attention Required! | Cloudflare")',
        default='Attention Required! | Cloudflare')

    # Parse the arguments
    argument_parser_args = parser.parse_args()

    # Transfer the arguments to a dictionary to be passed to run_test() function
    args = {}
    args['url'] = argument_parser_args.u
    args['captcha_sign'] = argument_parser_args.c
    args['tbb_path'] = argument_parser_args.t

    params = run_test(args)

    # Print the results when run from the command line
    print("tor:" + params.get('url') + ":" + str(params.get('result')))



# Handles given the argument list and runs the tests
def run_test(params):
    url = params.get('url')
    captcha_sign = params.get('captcha_sign')
    tbb_path = params.get('tbb_path')

    # Insert current UNIX time stamp
    params['time_stamp'] = int(time.time())

    # Run the test and return the results with other parameters
    params['result'] = launch_tb_with_stem(tbb_path, url, captcha_sign)

    return params



# Launch the given url in the browser and check if there is any captcha
def launch_tb_with_stem(tbb_dir, url, captcha_sign):
    with TorBrowserDriver(tbb_dir) as driver:
        driver.load_url(url)

        # Check if the captcha sign exists within the page
        if(captcha_sign in driver.page_source):
            return 1
        else:
            return 0



if __name__ == '__main__':
    main()
    sys.exit(0)
