from pathlib import Path
import os
import logging
import sys
import time
from captchamonitor.utils.queue import Queue
import captchamonitor.utils.tor_launcher as tor_launcher


def add(args):
    """
    Add a new job to the queue
    """
    logger = logging.getLogger(__name__)

    os.environ['CM_TOR_DIR_PATH'] = str(os.path.join(str(Path.home()), '.cm_tor', '0'))

    if args.verbose:
        logging.getLogger('captchamonitor').setLevel(logging.DEBUG)

    queue = Queue()

    if args.all_exit_nodes:

        wait_time = 3
        logger.info(
            'I\'m going to replicate the specified job for all exit nodes. Use CTRL+C if you want to cancel.')
        logger.info('I\'ll wait for %d seconds before starting, just in case' % wait_time)

        for i in range(wait_time, 0, -1):
            logger.info('%s' % i)
            time.sleep(1)

        logger.info('Started adding the jobs, might take a while')

        try:
            # Just all exit nodes
            tor = tor_launcher.TorLauncher()
            for exit in tor.get_exit_relays().keys():
                data = {'method': args.method,
                        'url': args.url,
                        'captcha_sign': args.captcha_sign,
                        'additional_headers': args.additional_headers,
                        'exit_node': exit,
                        'tbb_security_level': args.tbb_security_level,
                        'browser_version': args.browser_version,
                        'expected_hash': args.data_hash}
                queue.add_job(data)

            logger.info('Done!')

        except KeyboardInterrupt:
            logger.info('Stopping, bye!')

        except Exception as err:
            logging.error(err, exc_info=True)

    else:
        data = {'method': args.method,
                'url': args.url,
                'captcha_sign': args.captcha_sign,
                'additional_headers': args.additional_headers,
                'exit_node': args.exit_node,
                'tbb_security_level': args.tbb_security_level,
                'browser_version': args.browser_version,
                'expected_hash': args.data_hash}

        queue.add_job(data)
        logger.info('Done!')

    sys.exit()
