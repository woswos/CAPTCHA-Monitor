
"""
Check if a web site returns a CloudFlare CAPTCHA.

Original source code:
https://github.com/NullHypothesis/exitmap/blob/master/src/modules/cloudflared.py

Ported to python 3 and modified to work with regular websites instead of
TOR exit relays. Also added a cli interface.
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
import http.client
import collections
from io import BytesIO
import gzip
import logging
import zlib
import json
import datetime
from argparse import ArgumentParser

log = logging.getLogger(__name__)

# Mimic Tor Browser's request headers, so CloudFlare won't return a 403 because
# it thinks we are a bot.
# domain.name will be replaced with the actual domain name
http_headers = [("Host", "domain.name"),
                ("User-Agent", "Mozilla/5.0 (Windows NT 6.1; rv:52.0) "
                 "Gecko/20100101 Firefox/52.0"),
                ("Accept", "text/html,application/xhtml+xml,"
                           "application/xml;q=0.9,*/*;q=0.8"),
                ("Accept-Language", "en-US,en;q=0.5"),
                ("Accept-Encoding", "gzip"),
                ("Connection", "keep-alive"),
                ("Upgrade-Insecure-Requests", "1")]

encoding = 'utf-8'
timeout = 10


def main():
    desc = """Check if a web site returns a
    CloudFlare CAPTCHA using http.client. By default,
    searches for 'Attention Required! | Cloudflare'"""

    parser = ArgumentParser(description=desc)
    parser.add_argument('-d', metavar='domain', help='destination domain')
    parser.add_argument('-p', metavar='port', help='destination port')
    parser.add_argument('-c', metavar='captcha',
        help='the captcha sign expected to see in the page',
        default="Attention Required! | Cloudflare")
    args = parser.parse_args()

    domain = args.d
    port = args.p
    captcha_sign = args.c

    if port == 443:
        result = is_cloudflared(domain, port, timeout, captcha_sign, secured = True)
    else:
        result = is_cloudflared(domain, port, timeout, captcha_sign)

    print("http:" + domain + ":" + port + ":" + str(result))


def decompress(data):
    """
    Decompress gzipped HTTP response.
    """

    try:
        buf = BytesIO(data)
        fileobj = gzip.GzipFile(fileobj=buf)
        data = fileobj.read()
    except Exception:
        log.warning("Cannot decode the https response")
        return

    return data


def is_cloudflared(domain, port, timeout, captcha_sign, secured = False):
    if secured:
        conn = http.client.HTTPSConnection(domain, port, timeout=timeout)
    else:
        conn = http.client.HTTPConnection(domain, port, timeout=timeout)
    http_headers[0] = ("Host", domain)
    conn.request("GET", "/", headers=collections.OrderedDict(http_headers))

    try:
        response = conn.getresponse()
    except Exception as err:
        log.warning("urlopen() over %s says: %s" % (domain, err))
        return -1

    data = response.read()

    if(secured):
        data = decompress(data)

    if not data:
        log.warning("Did not get any data from %s." % domain)
        return -1

    data = data.decode(encoding)

    if (data.find(captcha_sign) != -1):
        log.info("Exit %s sees a CAPTCHA." % domain)
        return 1
    else:
        log.info("Exit %s does NOT see a CAPTCHA." % domain)
        return 0


if __name__ == "__main__":
    main()
    sys.exit(0)
