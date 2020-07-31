import email
import io
import json
import logging
import os
import signal
from selenium import webdriver


def force_quit_driver(driver):
    logger = logging.getLogger(__name__)

    pid = driver.service.process.pid

    # Close all windows
    for window in driver.window_handles:
        driver.switch_to.window(window)
        driver.close()

    # Quit the driver
    driver.quit()

    # Kill the process, just in case
    try:
        os.kill(int(pid), signal.SIGTERM)
        logger.debug("Force killed the process")

    except ProcessLookupError as ex:
        pass


def format_requests_tb(requests_data, url):
    logger = logging.getLogger(__name__)
    cleaned = {'data': []}
    for request in requests_data['data']:
        temp = {}

        # Skip the internal request to the browser extension
        if ('255.255.255.255' not in str(request['url'])) and ('chrome-extension' not in str(request['url'])):
            for key, value in request.items():
                if value != '':
                    temp[key] = parse_headers(value)

                # For some reason the extension doesn't include the URL of the
                #   original request. This puts the URL back.
                if 'url' not in temp:
                    temp['url'] = url

            cleaned['data'].append(temp)

    #logger.debug(json.dumps(cleaned, indent=4))

    return json.dumps(cleaned)


def format_requests_seleniumwire(requests_data):
    cleaned = {'data': []}
    for request in requests_data:
        temp = {}
        #temp['post_data'] = ''
        if request.headers is not None:
            temp['request_headers'] = dict(request.headers)
        if request.response is not None:
            temp['response_headers'] = dict(request.response.headers)
            temp['status_line'] = parse_headers(
                (str(request.method) + ': ' + str(request.response.status_code) + ' ' + str(request.response.reason)))
        if request.path is not None:
            temp['url'] = request.path
        cleaned['data'].append(temp)

    return json.dumps(dict(cleaned))


def format_requests_curl(request_headers, response_headers, status_line, url):
    cleaned = {'data': []}
    temp = {}
    temp['request_headers'] = request_headers
    temp['response_headers'] = response_headers
    temp['status_line'] = parse_headers('GET: ' + str(status_line))
    temp['url'] = url
    cleaned['data'].append(temp)

    return json.dumps(cleaned)


def format_requests_requests(request_headers, response_headers, status_code, url):
    cleaned = {'data': []}
    temp = {}
    temp['request_headers'] = request_headers
    temp['response_headers'] = response_headers
    temp['status_line'] = parse_headers('GET: ' + str(status_code))
    temp['url'] = url
    cleaned['data'].append(temp)

    return json.dumps(cleaned)


def parse_headers(raw_headers):
    # Check if the header is a single word string
    if ' ' in raw_headers:
        #request_line, headers_alone = request_text.split('\r\n', 1)
        message = email.message_from_file(io.StringIO(raw_headers))
        return dict(message.items())
    else:
        return raw_headers
