import logging
import sys
from random import randint
from threading import Timer
import time

def analyze(args):
    logger = logging.getLogger(__name__)

    if args.verbose:
        logging.getLogger('captchamonitor').setLevel(logging.DEBUG)
        global verbose
        verbose = True

    try:
        logger.info('Started running CAPTCHA Monitor Analyze')

        logger.info('Setting up the tasks...')

        tasks = []
        minute_multiplier = 60
        tasks.append(RepeatingTimer(args.new_relays * minute_multiplier,
                                    get_new_relays))

        for task in tasks:
            task.start()
            # To reduce the chance of simultaneus database access
            time.sleep(randint(10, 30))

        logger.debug('Done with the tasks, started looping...')

        while True:
            time.sleep(1)

    except Exception as err:
        logging.error(err, exc_info=True)

    except (KeyboardInterrupt, SystemExit):
        logger.info('Stopping CAPTCHA Monitor Analyze...')

    finally:
        logger.debug('Stopping the timed tasks...')
        # Stop the created tasks
        for task in tasks:
            task.cancel()

        logger.debug('Completely exitting...')
        sys.exit()


class Args(object):
    pass


class RepeatingTimer(Timer):
    def run(self):
        while not self.finished.is_set():
            self.function(*self.args, **self.kwargs)
            self.finished.wait(self.interval)
