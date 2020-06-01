from captchamonitor.chef import CaptchaMonitor
import logging

logger_format = '%(asctime)s %(module)s [%(levelname)s] %(message)s'
logging.basicConfig(format=logger_format)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

if __name__ == '__main__':

    config_file = '/home/woswos/CAPTCHA-Monitor/captchamonitor/resources/config.ini'

    while True:
        CaptchaMonitor.run(config_file)
