import hashlib
import logging
import sys

from captchamonitor.utils.fetch import fetch_via_method


def md5(args):
    """
    Returns the MD5 hash of a given URL
    """

    logger = logging.getLogger(__name__)

    url = args.url

    if args.verbose:
        logging.getLogger("captchamonitor").setLevel(logging.DEBUG)

    job = {
        "method": "firefox",
        "url": url,
        "captcha_sign": "",
        "additional_headers": "",
        "exit_node": "",
        "tbb_security_level": "",
        "browser_version": "",
    }

    try:
        logger.info("Fetching %s" % url)
        fetched_data_1 = fetch_via_method(job)
        logger.debug("Fetching %s one more time to confirm" % url)
        fetched_data_2 = fetch_via_method(job)
        logger.debug("OK, this is the last one")
        fetched_data_3 = fetch_via_method(job)

        if (fetched_data_1["html_data"] == fetched_data_2["html_data"]) and (
            fetched_data_2["html_data"] == fetched_data_3["html_data"]
        ):
            hash = hashlib.md5(
                fetched_data_1["html_data"].encode("utf-8")
            ).hexdigest()
            logger.info("Hash of %s is: %s" % (url, hash))
        else:
            logger.info("Please try one more time")

    except KeyboardInterrupt:
        logger.info("Stopping, bye!")

    except Exception as err:
        logger.info("An error occurred: %s" % err)

    finally:
        sys.exit()
