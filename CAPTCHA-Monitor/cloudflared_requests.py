#!/usr/bin/env python2

"""
Check if a web site returns a CloudFlare CAPTCHA using the requests library
"""


import sys
# Throw an error if user is trying to use Python 2.7 or older
if not (sys.version_info[0] > 2.7):
    raise Exception("Please use Python 3+")

from argparse import ArgumentParser
from urllib.parse import urlparse
import time
import requests
import logging
import json

logger_format = '%(asctime)s :: %(module)s :: %(levelname)s :: %(message)s'
logging.basicConfig(format=logger_format)
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


# Returns a dictionary of parameters including the result
# Result is 0 if CloudFlare captcha is not detected
# Result is if CloudFlare captcha is detected
# Result is -1 if an error occurred
def main():
    # ArgumentParser details
    desc = """Check if a web site returns a CloudFlare CAPTCHA using requests.
     By default, this tool is looking for the 'Cloudflare' text within the
     fetched web site.
    """
    parser = ArgumentParser(description=desc)
    parser.add_argument('-u', metavar='url', help='destination url',
        required=True)
    parser.add_argument('-c', metavar='captcha',
        help='the captcha sign expected to see in the page (default: "Cloudflare")',
        default='Cloudflare')
    parser.add_argument('-r', metavar='headers',
        help='use this argument to place any custom headers you want to include',
        default=None)

    # Parse the arguments
    argument_parser_args = parser.parse_args()

    # Transfer the arguments to a dictionary to be passed to run_test() function
    args = {}
    args['url'] = argument_parser_args.u
    args['captcha_sign'] = argument_parser_args.c
    # Parse the given headers
    if(argument_parser_args.r != None):
        args['headers'] = json.loads(argument_parser_args.r)

    # Run the test
    params = is_cloudflared(args)

    # Print the results when run from the command line
    result = "requests;" + params.get('url') + ";" + str(params.get('result'))
    logger.info(result)
    print(result)


# Handles given the argument list and runs the test
def is_cloudflared(params):
    url = params.get('url')
    captcha_sign = params.get('captcha_sign')
    headers = params.get('headers')

    # Insert current UNIX time stamp
    params['time_stamp'] = int(time.time())
    params['method'] = 'requests'

    # Run the test and return the results with other parameters
    params['result'] = test_url(url, captcha_sign, headers)

    return params


# Check if site returns a CloudFlare CAPTCHA
def test_url(url, captcha_sign, headers):
    # Try sending a request to the server and get server's response
    try:
        data = requests.get(url, headers=headers)

    except Exception as err:
        logger.error('Double check the url you have entered because request.get() says: %s' % err)
        return -1

    # Check if the captcha sign exists within the page
    return int(data.text.find(captcha_sign) > 0)


if __name__ == '__main__':
    main()
    sys.exit(0)
