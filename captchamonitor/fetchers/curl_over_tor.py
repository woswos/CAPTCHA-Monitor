"""
Fetch a given URL via cURL using PycURL and Tor
"""

import logging
import pycurl
from io import BytesIO
import json
import captchamonitor.utils.tor_launcher as tor_launcher

logger = logging.getLogger(__name__)

headers = {}


def fetch_via_curl_over_tor(url, tor_socks_host, tor_socks_port, additional_headers=None, exit_node=None, **kwargs):

    tor_process = tor_launcher.launch_tor_with_config(tor_socks_port, exit_node)

    # Wait until Tor starts
    while(not tor_launcher.is_tor_running(tor_socks_port)):
        pass

    results = {}
    temp = []
    default_curl_request_headers = {"host": url, "user-agent": "curl/7.58.0", "accept": "*/*"}

    b_obj = BytesIO()
    curl = pycurl.Curl()

    curl.setopt(pycurl.PROXY, tor_socks_host)
    curl.setopt(pycurl.PROXYPORT, int(tor_socks_port))
    curl.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_SOCKS5)

    curl.setopt(curl.URL, url)
    curl.setopt(curl.WRITEDATA, b_obj)
    # Use the default curl user agent
    curl.setopt(pycurl.USERAGENT, 'curl/7.58.0')

    # Parse the provided additional headers
    if additional_headers:
        additional_headers = json.loads(additional_headers)

        # Convert the JSON into a list that pycurl wants
        for element in additional_headers:
            # user agent requires special treatment
            if element.lower() == 'user-agent':
                curl.setopt(pycurl.USERAGENT, str(additional_headers[element]))
                default_curl_request_headers[element.lower()] = str(additional_headers[element])
            else:
                temp.append(str(element + ': ' + additional_headers[element]))
                default_curl_request_headers[element.lower()] = str(additional_headers[element])

    additional_headers = temp

    curl.setopt(pycurl.HTTPHEADER, additional_headers)
    curl.setopt(curl.HEADERFUNCTION, parse_headers)
    #curl.setopt(pycurl.VERBOSE, 1)

    # Try sending a request to the server and get server's response
    try:
        curl.perform()

    except Exception as err:
        logger.error('pycurl.perform() says: %s' % err)
        return None

    data = b_obj.getvalue().decode('utf8')

    results['request_headers'] = json.dumps(default_curl_request_headers)
    results['html_data'] = str(data)
    results['all_headers'] = str(curl.getinfo(pycurl.RESPONSE_CODE))
    results['response_headers'] = str(headers)

    logger.debug('I\'m done fetching %s', url)

    curl.close()

    tor_launcher.kill(tor_process)

    return results


def parse_headers(header):
    header = header.decode('iso-8859-1')

    # Ignore all lines without a colon
    if ':' not in header:
        return

    # Break the header line into header name and value
    header_name, header_value = header.split(':', 1)

    # Remove whitespace that may be present
    header_name = header_name.strip()
    header_value = header_value.strip()
    headers[header_name] = header_value
