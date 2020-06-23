import logging


def detect(captcha_sign, data):
    logger = logging.getLogger(__name__)
    return (captcha_sign.lower() in data.lower())
