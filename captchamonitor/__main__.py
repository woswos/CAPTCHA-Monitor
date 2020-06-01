from captchamonitor.chef import CaptchaMonitor
import logging

logger_format = '%(asctime)s %(module)s [%(levelname)s] %(message)s'
logging.basicConfig(format=logger_format)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

if __name__ == '__main__':

    logger.info('Found a new request in the queue, cooking...')

    #http://check.torproject.org
    url = 'https://check.torproject.org'
    headers = '{"user-agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:57.0) Gecko/20100101 Firefox/57.0"}'

    cm = CaptchaMonitor('firefox_with_tor')
    cm.create_params()
    cm.fetch(url, headers)
    cm.detect_captcha()
    cm.store()

    logger.info('Done, Bon Appetit!')
