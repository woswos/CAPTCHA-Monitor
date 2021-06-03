# import time
# import schedule
import logging
import argparse

from captchamonitor.cm import CaptchaMonitor

parser = argparse.ArgumentParser(description="CAPTCHA Monitor")
parser.add_argument(
    "-w",
    "--worker",
    action="store_true",
    default=False,
    help="Run an instance of worker",
)
args = parser.parse_args()

# Get the root logger for the package
logging.basicConfig(format="%(asctime)s %(module)s [%(levelname)s] %(message)s")
logger = logging.getLogger("captchamonitor")
logger.setLevel(logging.DEBUG)

# Run in the specified mode
if args.worker:
    logger.info("Intializing CAPTCHA Monitor in worker mode")
    CaptchaMonitor().worker()

# Schedule tasks
# logger.info("Scheduling tasks")
# schedule.every(0.5).seconds.do(cm.worker)

# # Run jobs
# logger.info("Started running the tasks")
# while True:
#     schedule.run_pending()
#     time.sleep(1)
