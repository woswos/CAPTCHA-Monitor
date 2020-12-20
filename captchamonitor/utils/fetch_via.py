import logging
import os
import tarfile
import tempfile

import requests

from captchamonitor.fetchers import firefox, tor_browser


def fetch_via_method(data, filesystem_folder_for_methods, timeout=30):
    """
    Fetches a website using the specified web browser or tool

    :param data: [description]
    :type data: [type]
    :param timeout: [description], defaults to 30
    :type timeout: int, optional
    """

    logger = logging.getLogger(__name__)

    method = data["method"]
    url = data["url"]
    additional_headers = data["additional_headers"]
    tbb_security_level = data["tbb_security_level"]
    method_version = data["browser_version"]

    method_to_folder = {
        "tor_browser": "tor_browser",
        "firefox": "firefox",
        "firefox_over_tor": "firefox",
        "chromium": "chromium",
        "chromium_over_tor": "chromium",
        "brave": "brave",
        "brave_over_tor": "brave",
        "curl": "curl",
        "curl_over_tor": "curl",
        "requests": "requests",
        "requests_over_tor": "requests",
    }

    # Find the file system path to the requested method
    method_path = os.path.join(
        filesystem_folder_for_methods, method_to_folder[method]
    )
    method_path_with_version = os.path.join(method_path, method_version)

    # Check if the requested method and version exists
    if not os.path.exists(method_path_with_version):
        logger.warning(
            "The specified method version %s for %s does not exist locally, will try to download",
            method_version,
            method,
        )

        # Try to download the requested method
        download_method_to(method, method_version, method_path_with_version)

    logger.debug('Fetching "%s" via "%s" - "v%s"', url, method, method_version)

    results = {"browser_version": method_version}

    # Fetch the URL via requested method
    if "tor_browser" in method:
        fetcher_handle = tor_browser.TorBrowser(
            url=url,
            fetcher_path=method_path_with_version,
            additional_headers=additional_headers,
            security_level=tbb_security_level,
            timeout=timeout,
        )

    elif "firefox" in method:
        fetcher_handle = firefox.Firefox(
            url=url,
            fetcher_path=method_path_with_version,
            additional_headers=additional_headers,
            timeout=timeout,
        )

    fetcher_handle.setup()
    fetcher_handle.fetch()

    results["html_data"] = fetcher_handle.html_data
    results["requests"] = fetcher_handle.requests

    return results


def download_method_to(method, method_version, method_path_with_version):
    """
    Downloads the specified version of the specified method to the specified
    system folder.

    :param method: The type of web browser that needs to be downloaded
    :type method: str
    :param method_version: Requested version of the method
    :type method_version: str
    :param method_path_with_version: Absolute path to the filesystem folder where web browser need to be stored
    :type method_path_with_version: str
    :raises Exception: If provided method is not supported yet
    :raises Exception: If provided method version doesn't exist
    """

    logger = logging.getLogger(__name__)

    # Get the correct download URL
    if "tor_browser" in method:
        url = (
            "https://archive.torproject.org/tor-package-archive/torbrowser/%s/tor-browser-linux64-%s_en-US.tar.xz"
            % (method_version, method_version)
        )

    elif "firefox" in method:
        url = (
            "https://ftp.mozilla.org/pub/firefox/releases/%s/linux-x86_64/en-US/firefox-%s.tar.bz2"
            % (method_version, method_version)
        )

    else:
        raise Exception("Provided method is not supported yet")

    # Check if the URL makes sense and exists
    if not is_downloadable(url):
        raise Exception("Seems like the provided method version doesn't exist")

    with tempfile.NamedTemporaryFile() as temp_save:
        # Now download the content
        logger.debug("Started downloading")
        req = requests.get(url, allow_redirects=True)
        temp_save.write(req.content)

        # Extract the archive to method_path_with_version
        logger.debug("Extracting the archive")
        archive = tarfile.open(temp_save.name)
        archive.extractall(method_path_with_version)
        archive.close()

    logger.info("Managed to download version %s for %s", method_version, method)


def is_downloadable(url):
    """
    Does the url contain a downloadable resource

    :param url: URL to check
    :type url: str
    :return: If the URL contains a downloadable resource
    :rtype: bool
    """

    head = requests.head(url, allow_redirects=True)
    header = head.headers
    content_type = header.get("content-type")

    if "text" in content_type.lower():
        return False
    if "html" in content_type.lower():
        return False

    return True
