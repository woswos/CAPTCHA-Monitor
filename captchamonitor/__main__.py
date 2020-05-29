from captchamonitor.chef import CaptchaMonitor
import logging

logger_format = '%(asctime)s :: %(module)s :: %(levelname)s :: %(message)s'
logging.basicConfig(format=logger_format)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

if __name__ == '__main__':
    print('Starting to cook...')

    url = "https://example.com/"

    cm = CaptchaMonitor('tor')
    cm.create_params()
    cm.fetch(url)
    cm.detect_captcha()
    cm.store()

    print('Ready to serve')
