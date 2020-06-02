from captchamonitor.chef import CaptchaMonitor
import logging
import time
import argparse

logger_format = '%(asctime)s %(module)s [%(levelname)s] %(message)s'
logging.basicConfig(format=logger_format)
logger = logging.getLogger('captchamonitor')
logger.setLevel(logging.INFO)


def main():
    logger.info('Running CAPTCHA Monitor with the given configuration file')
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', dest='config_file', help='Absolute path to the configuration file', required=True)
    args = parser.parse_args()
    config_file = args.config_file

    while True:
        CaptchaMonitor.run(config_file)
        time.sleep(1)


if __name__ == '__main__':
    main()
