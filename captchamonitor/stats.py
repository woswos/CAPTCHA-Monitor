import logging
import sys
import time

from captchamonitor.utils.queue import Queue


def stats(args):
    logger = logging.getLogger(__name__)

    if args.verbose:
        logging.getLogger("captchamonitor").setLevel(logging.DEBUG)

    queue = Queue()
    remaining_jobs = queue.count_remaining_jobs()
    # Using a conservative 16 seconds per job average
    estimated_hours = remaining_jobs * 16
    logger.info("There are:")
    logger.info("> %s job(s) in the queue", remaining_jobs)
    logger.info("> %s completed job(s)", queue.count_completed_jobs())
    logger.info("> %s failed job(s)", queue.count_failed_jobs())
    logger.info(
        "> It would approximately take %s to complete the job(s) *time format is hh:mm:ss*",
        time.strftime("%H:%M:%S", time.gmtime(estimated_hours)),
    )
    sys.exit()
