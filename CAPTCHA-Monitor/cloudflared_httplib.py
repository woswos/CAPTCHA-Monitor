#!/usr/bin/env python2

"""
Check if a web site returns a CloudFlare CAPTCHA using http.client

Original source code:
https://github.com/NullHypothesis/exitmap/blob/master/src/modules/cloudflared.py

Modified to work with regular websites instead of TOR exit relays.
Also added a cli interface.

See the original license below:
"""

# Copyright 2016 Philipp Winter <phw@nymity.ch>
#
# This file is part of exitmap.
#
# exitmap is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# exitmap is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with exitmap.  If not, see <http://www.gnu.org/licenses/>.

import sys
# Throw an error if user is trying to use Python 3 or newer
if sys.version_info[0] > 2.7:
    raise Exception("Please use Python 2.7")

from argparse import ArgumentParser
from urlparse import urlparse
import time
import StringIO
import gzip
import httplib
import collections
import logging

logger_format = '%(asctime)s :: %(module)s :: %(levelname)s :: %(message)s'
logging.basicConfig(format=logger_format)
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


# Mimic Tor Browser's request headers, so CloudFlare won't return a 403 because
# it thinks we are a bot.
# "domai.name" is replaced automatically with the passed domain name
default_headers = [("Host", "domain.name"),
                   ("User-Agent", "Mozilla/5.0 (Windows NT 6.1; rv:52.0) "
                    "Gecko/20100101 Firefox/52.0"),
                   ("Accept", "text/html,application/xhtml+xml,"
                    "application/xml;q=0.9,*/*;q=0.8"),
                   ("Accept-Language", "en-US,en;q=0.5"),
                   ("Accept-Encoding", "gzip, deflate, br"),
                   ("Connection", "keep-alive"),
                   ("Upgrade-Insecure-Requests", "1")]


# Returns a dictionary of parameters including the result
# Result is 0 if CloudFlare captcha is not detected
# Result is if CloudFlare captcha is detected
# Result is -1 if an error occurred
def main():
    # ArgumentParser details
    desc = """Check if a web site returns a CloudFlare CAPTCHA using httplib.
     By default, this tool is looking for the 'Cloudflare' text within the
     fetched web site.
    """
    parser = ArgumentParser(description=desc)
    parser.add_argument('-u', metavar='url', help='destination url',
                        required=True)
    parser.add_argument('-c', metavar='captcha',
                        help='the captcha sign expected to see in the page (default: "Cloudflare")',
                        default='Cloudflare')

    # Parse the arguments
    argument_parser_args = parser.parse_args()

    # Transfer the arguments to a dictionary to be passed to run_test() function
    args = {}
    args['url'] = argument_parser_args.u
    args['captcha_sign'] = argument_parser_args.c

    # Run the test
    params = is_cloudflared(args)

    # Print the results when run from the command line
    result = "httplib;" + params.get('url') + ";" + str(params.get('result'))
    logger.info(result)
    print(result)


# Handles the given argument list and runs the test
def is_cloudflared(params):
    url = params.get('url')

    # Parse the given url to get different sections
    parsed_uri = urlparse(url)
    domain = '{uri.netloc}'.format(uri=parsed_uri)
    path = '{uri.path}'.format(uri=parsed_uri)
    scheme = '{uri.scheme}'.format(uri=parsed_uri)

    # If no path is specified, use the default path
    if(path == ''):
        path = '/'

    # Set the https flag based on the provided url
    https = (scheme == 'https')
    captcha_sign = params.get('captcha_sign')

    # Replace the place holder url in the header
    default_headers[0] = ("Host", domain)

    # Replace the whole header if provided
    if(params.get('headers') != None):
        headers = params.get('headers')
    else:
        headers = default_headers

    # Insert current UNIX time stamp
    params['time_stamp'] = int(time.time())
    params['method'] = 'httplib'

    # Run the test and return the results with other parameters
    params['result'] = test_url(url, https, domain, path, captcha_sign, headers)

    return params


# Check if site returns a CloudFlare CAPTCHA
def test_url(url, https, domain, path, captcha_sign, headers):
    # Decide on which protocol to use
    if https:
        conn = httplib.HTTPSConnection(domain)
    else:
        conn = httplib.HTTPConnection(domain)

    # Try sending a request to the server
    try:
        conn.request('GET', path, headers=collections.OrderedDict(headers))

    except Exception as err:
        logger.error('Double check the url you have entered because request() says: %s' % err)
        return -1

    # Get server's response
    try:
        response = conn.getresponse()
    except Exception as err:
        logger.error('urlopen() over %s says: %s' % (url, err))
        return -1

    # Decompress the compressed response
    data = decompress(response.read())
    if not data:
        logger.error('Did not get any data over %s' % url)
        return -1

    # Check if the captcha sign exists within the page
    if(captcha_sign in data):
        return 1
    else:
        return 0


# Decompress gzipped HTTP response.
def decompress(data):
    try:
        buf = StringIO.StringIO(data)
        fileobj = gzip.GzipFile(fileobj=buf)
        data = fileobj.read()
    except Exception:
        pass

    return data


if __name__ == '__main__':
    main()
    sys.exit(0)
