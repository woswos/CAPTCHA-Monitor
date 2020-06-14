import pytest
import logging

logger_format = '%(asctime)s %(module)s [%(levelname)s] %(message)s'
logging.basicConfig(format=logger_format)
logger = logging.getLogger('captchamonitor')
logger.setLevel(logging.DEBUG)
logger = logging.getLogger('stem')
logger.setLevel(logging.INFO)
logger = logging.getLogger('log')
logger.setLevel(logging.INFO)
