from captchamonitor.chef import CaptchaMonitor
import logging

logger_format = '%(asctime)s :: %(module)s :: %(levelname)s :: %(message)s'
logging.basicConfig(format=logger_format)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

if __name__ == '__main__':

    logger.info('Found a new request in the queue, cooking...')

    url = 'https://bypass.captcha.wtf/'
    headers = '{"user-agent": "Mozilla/5.0 (Windows NT 10.0; rv:68.0) Gecko/20100101 Firefox/68.0"}'

    cm = CaptchaMonitor('tor')
    cm.create_params()
    cm.fetch(url, headers)
    cm.detect_captcha()
    cm.store()

    logger.info('Done, Bon Appetit!')
