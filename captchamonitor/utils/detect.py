import logging
import hashlib


def captcha(captcha_sign, data):
    logger = logging.getLogger(__name__)
    return int(captcha_sign.lower() in data.lower())


def diff(expected_hash, received_data):
    logger = logging.getLogger(__name__)

    # Do not diff if it wasn't asked
    if(expected_hash == ''):
        return ''
    else:
        hash_value = hashlib.md5(received_data.encode("utf-8")).hexdigest()
        return int(expected_hash != hash_value)
