import time
import logging
import argparse

import schedule

from captchamonitor.cm import CaptchaMonitor

parser = argparse.ArgumentParser(description="CAPTCHA Monitor")
parser.add_argument(
    "-w",
    "--worker",
    action="store_true",
    default=False,
    help="Run an instance of worker",
)
parser.add_argument(
    "-u",
    "--update",
    action="store_true",
    default=False,
    help="Update the URLs and relays in the database",
)
args = parser.parse_args()

# Get the root logger for the package
logging.basicConfig(format="%(asctime)s %(module)s [%(levelname)s] %(message)s")
logger = logging.getLogger("captchamonitor")
logger.setLevel(logging.DEBUG)

cm = CaptchaMonitor()

# Run in the specified mode
if args.worker:
    logger.info("Intializing CAPTCHA Monitor in worker mode")
    cm.worker()
elif args.update:
    logger.info("Intializing CAPTCHA Monitor in update mode")
    schedule.every().day.do(cm.update_domains)
    schedule.every().hour.do(cm.update_relays)
    schedule.every().day.do(cm.update_fetchers)

# Run all scheduled jobs at the beginning
schedule.run_all()

# Run jobs at the scheduled times
while True:
    schedule.run_pending()
    time.sleep(1)
