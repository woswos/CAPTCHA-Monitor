import email
import glob
import io
import json
import logging
import os
import pathlib
import signal
import tempfile
import time

import captchamonitor.utils.exceptions as exceptions


class BaseFetcher:
    """
    The base fetcher class that contains tools that will be used by other fetchers.
    Also establishes a common framework for standardization.
    """

    def __init__(self, url, fetcher_path, additional_headers=None, timeout=30):
        """
        Constructor

        :param url: The website URL to fetch including the URL scheme
        :type url: str
        :param fetcher_path: The absolute path to folder on the file system that contains the fetcher binary
        :type fetcher_path: str
        :param additional_headers: The headers to overwrite while performing requests, defaults to None
        :type additional_headers: dict, optional
        :param timeout: Maximum time allowed for a web page to load, defaults to 30
        :type timeout: int, optional
        :raises exceptions.MissingEnvVar: If a required environment variable is missing
        """
        self.logger = logging.getLogger(__name__)

        try:
            self.tor_socks_host = os.environ["CM_TOR_HOST"]
            self.tor_socks_port = os.environ["CM_TOR_SOCKS_PORT"]

        except Exception as err:
            self.logger.error(
                "Some of the environment variables are missing: %s", err
            )
            raise exceptions.MissingEnvVar

        self.url = url
        self.fetcher_path = fetcher_path
        self.additional_headers = additional_headers
        self.timeout = timeout

        self.download_folder = tempfile.TemporaryDirectory()
        self.html_data = None
        self.requests = None
        self.driver = None
        self.requests_data = None
        self.binary = None
        self.profile = None
        self.options = None

        # Prepare HTTP Header Live Extension
        self.http_header_live_export_file = os.path.join(
            self.download_folder.name, "captcha_monitor_website_data.json"
        )

        self.http_header_live_folder = "../assets/http_header_live/"
        script_path = pathlib.Path(__file__).parent.absolute()

        # Find the right extension for Firefox and derivatives
        search_string_xpi = os.path.abspath(
            os.path.join(script_path, self.http_header_live_folder, "*.xpi")
        )
        self.http_header_live_extension_xpi = glob.glob(search_string_xpi)[0]

        # Find the right extension for Chromium and derivatives
        search_string_crx = os.path.abspath(
            os.path.join(script_path, self.http_header_live_folder, "*.crx")
        )
        self.http_header_live_extension_crx = glob.glob(search_string_crx)[0]

        # Delete the previous HTTP-Header-Live export
        if os.path.exists(self.http_header_live_export_file):
            os.remove(self.http_header_live_export_file)

    def __del__(self):
        """
        Cleanup before destructing the object
        """

        # Remove the temporary download folder
        self.download_folder.cleanup()

    def parse_headers_via_http_header_live_extension(self):
        """
        Parses the header file exported from the HTTP-Header-Live extension

        :raises exceptions.HTTPHeaderLiveErr: If the extension was not successful
        """

        # Wait for HTTP-Header-Live extension to finish
        self.logger.debug("Waiting for HTTP-Header-Live extension")
        for _ in range(self.timeout):
            try:
                with open(self.http_header_live_export_file) as file:
                    self.requests_data = json.load(file)
                    break

            except OSError:
                # Wait for a second if the file is not there yet
                time.sleep(1)

            except Exception as err:
                self.force_quit_driver(self.driver)
                self.logger.error("Cannot parse the headers: %s", err)

        if self.requests_data is None:
            self.force_quit_driver(self.driver)
            # Don't return anything since we couldn't capture the headers
            self.logger.error(
                "Couldn't capture the headers from %s",
                self.http_header_live_export_file,
            )
            raise exceptions.HTTPHeaderLiveCaptureErr

    def force_quit_driver(self, driver):
        """
        Force quits the given selenium webdriver

        :param driver: The webdriver to kill
        :type driver: wedriver.driver()
        """

        self.logger = logging.getLogger(__name__)

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
            self.logger.debug("Force killed the process")

        except ProcessLookupError:
            pass

    def parse_headers(self, raw_headers):
        # Check if the header is a single word string
        if " " in raw_headers:
            # request_line, headers_alone = request_text.split('\r\n', 1)
            message = email.message_from_file(io.StringIO(raw_headers))
            return dict(message.items())

        return raw_headers

    def format_requests_tb(self, requests_data, url):
        cleaned = {"data": []}
        for request in requests_data["data"]:
            temp = {}

            # Skip the internal request to the browser extension
            if ("255.255.255.255" not in str(request["url"])) and (
                "chrome-extension" not in str(request["url"])
            ):
                for key, value in request.items():
                    if value != "":
                        temp[key] = self.parse_headers(value)

                    # For some reason the extension doesn't include the URL of the
                    #   original request. This puts the URL back.
                    if "url" not in temp:
                        temp["url"] = url

                cleaned["data"].append(temp)

        # logger.debug(json.dumps(cleaned, indent=4))

        return json.dumps(cleaned)

    def format_requests_seleniumwire(self, requests_data):
        cleaned = {"data": []}
        for request in requests_data:
            temp = {}
            # temp['post_data'] = ''
            if request.headers is not None:
                temp["request_headers"] = dict(request.headers)
            if request.response is not None:
                temp["response_headers"] = dict(request.response.headers)
                temp["status_line"] = self.parse_headers(
                    (
                        str(request.method)
                        + ": "
                        + str(request.response.status_code)
                        + " "
                        + str(request.response.reason)
                    )
                )
            if request.path is not None:
                temp["url"] = request.path
            cleaned["data"].append(temp)

        return json.dumps(dict(cleaned))

    def format_requests_curl(
        self, request_headers, response_headers, status_line, url
    ):
        cleaned = {"data": []}
        temp = {}
        temp["request_headers"] = request_headers
        temp["response_headers"] = response_headers
        temp["status_line"] = self.parse_headers("GET: " + str(status_line))
        temp["url"] = url
        cleaned["data"].append(temp)

        return json.dumps(cleaned)

    def format_requests_requests(
        self, request_headers, response_headers, status_code, url
    ):
        cleaned = {"data": []}
        temp = {}
        temp["request_headers"] = request_headers
        temp["response_headers"] = response_headers
        temp["status_line"] = self.parse_headers("GET: " + str(status_code))
        temp["url"] = url
        cleaned["data"].append(temp)

        return json.dumps(cleaned)
