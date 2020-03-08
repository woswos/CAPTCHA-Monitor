#!/usr/bin/env python

"""
Check if a web site returns a CloudFlare CAPTCHA using selenium and Tor browser

Used library: https://github.com/webfp/tor-browser-selenium
"""

from argparse import ArgumentParser
from tbselenium.tbdriver import TorBrowserDriver
import tbselenium.common as cm
from tbselenium.utils import start_xvfb, stop_xvfb
from tbselenium.utils import launch_tbb_tor_with_stem
from selenium.webdriver.support.ui import Select
from time import sleep


# Launch the given url in the browser and check if there is any captcha
def launch_tb_with_stem(tbb_dir, url, captcha_sign):
    tor_process = launch_tbb_tor_with_stem(tbb_path=tbb_dir)
    # start a virtual display
    xvfb_display = start_xvfb()
    with TorBrowserDriver(tbb_dir) as driver:
        driver.load_url(url)
        if(captcha_sign in driver.page_source):
            result = 1
        else:
            result = 0

    tor_process.kill()

    return result


def main():
    desc = """Check if a web site returns a
    CloudFlare CAPTCHA using tor browser"""

    parser = ArgumentParser(description=desc)
    parser.add_argument('-d', metavar='domain', help='destination domain')
    parser.add_argument('-p', metavar='port', help='destination port')
    parser.add_argument('-c', metavar='captcha',
        help='the captcha sign expected to see in the page',
        default="Attention Required! | Cloudflare")
    parser.add_argument('-t', metavar='tor browser',
        help='path to tor browser bundle')
    args = parser.parse_args()

    domain = args.d
    port = args.p
    captcha_sign = args.c
    tbb_path = args.t

    if port == 443:
        url = "https://" + domain
    else:
        url = "http://" + domain

    result = launch_tb_with_stem(tbb_path, url, captcha_sign)

    print("tor:" + domain + ":" + port + ":" + str(result))


if __name__ == '__main__':
    main()
