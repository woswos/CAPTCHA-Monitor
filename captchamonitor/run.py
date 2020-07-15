import multiprocessing
from pathlib import Path
import port_for
import shutil
import logging
import os
import sys
import time
from threading import Timer
from stem.util.log import get_logger
from captchamonitor.utils.queue import Queue
from captchamonitor import worker

# Capture program start time
start_time = time.time()
last_remaining_jobs = 0


def run(args):
    logger = logging.getLogger(__name__)

    # Silence the stem logger
    stem_logger = get_logger()
    stem_logger.propagate = False

    # Get the args
    loop = args.loop
    clean = args.clean
    worker_count = args.worker
    retry_budget = args.retry
    timeout_value = int(args.timeout)
    heartbeat_interval = int(args.heartbeat)

    if args.verbose:
        logging.getLogger('captchamonitor').setLevel(logging.DEBUG)
    else:
        logging.getLogger('connectionpool').setLevel(logging.ERROR)
        logging.getLogger('urllib3').setLevel(logging.ERROR)

    try:
        # Start the heartbeat message timer (convert minutes to seconds)
        heartbeat = RepeatingTimer(heartbeat_interval * 60, heartbeat_message)
        heartbeat.start()

        if loop:
            logger.info('Started running in the continous mode with %s worker(s)' %
                        worker_count)
        else:
            logger.info('Started running with %s worker(s)' % worker_count)

        # Create the base path for the Tor directory
        worker_tor_base_dir = os.path.join(str(Path.home()), 'captchamonitor')
        if not os.path.exists(worker_tor_base_dir):
            os.mkdir(worker_tor_base_dir)

        elif clean:
            # if exits, delete the existing one and recreate it
            shutil.rmtree(worker_tor_base_dir)
            os.mkdir(worker_tor_base_dir)
            logger.info('Cleaned the existing Tor directory')

        # Spawn workers
        p = multiprocessing.Pool(worker_count)
        for w_id in range(worker_count):
            env_var = {'CM_WORKER_ID': w_id,
                       'CM_TOR_HOST': '127.0.0.1',
                       # 'CM_TOR_SOCKS_PORT': port_for.select_random(),
                       # 'CM_TOR_CONTROL_PORT': port_for.select_random(),
                       'CM_TOR_DIR_PATH': os.path.join(worker_tor_base_dir, str(w_id))
                       }

            p.apply_async(worker, args=(loop, env_var, retry_budget, timeout_value))

        p.close()
        p.join()

    except Exception as err:
        logging.error(err, exc_info=True)

    except (KeyboardInterrupt, SystemExit):
        logger.info('Stopping CAPTCHA Monitor...')
        # Force join process to shutdown
        p.close()
        p.join()

    finally:
        logger.debug('Stopping the heartbeat...')
        # Stop the heart beat
        heartbeat.cancel()

        logger.debug('Completely exitting...')
        sys.exit()


def heartbeat_message():
    global last_remaining_jobs

    logger = logging.getLogger('captchamonitor')

    queue = Queue()

    if last_remaining_jobs != 0:
        remaining_jobs = queue.count_remaining_jobs()

        seconds = time.time() - start_time
        seconds_in_day = 60 * 60 * 24
        seconds_in_hour = 60 * 60
        seconds_in_minute = 60

        days = seconds // seconds_in_day
        hours = (seconds - (days * seconds_in_day)) // seconds_in_hour
        minutes = (seconds - (days * seconds_in_day) -
                   (hours * seconds_in_hour)) // seconds_in_minute

        logger.info('Heartbeat: It has been %s days, %s hours, %s minutes ' % (
                    int(days), int(hours), int(minutes)))
        logger.info('> There are %s job(s) in the queue.' % remaining_jobs)
        logger.info('> I processed %s job(s) since the last heartbeat' % (
                    last_remaining_jobs - remaining_jobs))
        last_remaining_jobs = remaining_jobs

    else:
        last_remaining_jobs = queue.count_remaining_jobs()


class RepeatingTimer(Timer):
    def run(self):
        while not self.finished.is_set():
            self.function(*self.args, **self.kwargs)
            self.finished.wait(self.interval)
