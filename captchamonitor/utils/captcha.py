import logging

logger = logging.getLogger(__name__)


def detect(captcha_sign, data):
    return (captcha_sign.lower() in data.lower())
