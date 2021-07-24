import time
import logging
import argparse
from random import randint

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
    "-a",
    "--analyzer",
    action="store_true",
    default=False,
    help="Run an instance of data analyzer",
)
parser.add_argument(
    "-u",
    "--updater",
    action="store_true",
    default=False,
    help="Update the URLs and relays in the database",
)
parser.add_argument(
    "-d",
    "--dashboard",
    action="store_true",
    default=False,
    help="Update the static dashboard code",
)
args = parser.parse_args()

# Get the root logger for the package
logging.basicConfig(format="%(asctime)s %(module)s [%(levelname)s] %(message)s")
logger = logging.getLogger("captchamonitor")
logger.setLevel(logging.DEBUG)

# Add a random startup delay to prevent possible race conditions
time.sleep(randint(1, 5))

cm = CaptchaMonitor()

# Run in the specified mode
if args.worker:
    logger.info("Intializing CAPTCHA Monitor in worker mode")
    cm.worker()
elif args.analyzer:
    logger.info("Intializing CAPTCHA Monitor in data analysis mode")
    cm.analyzer()
elif args.updater:
    logger.info("Intializing CAPTCHA Monitor in update mode")
    schedule.every().day.do(cm.update_domains)
    schedule.every().hour.do(cm.update_relays)
    schedule.every().hour.do(cm.update_proxies)
    schedule.every().day.do(cm.update_fetchers)
    schedule.every().hour.do(cm.schedule_jobs)
elif args.dashboard:
    logger.info("Intializing CAPTCHA Monitor in dashboard update mode")
    schedule.every(30).minutes.do(cm.render_dashboard)

# Run all scheduled jobs at the beginning
schedule.run_all()

# Run jobs at the scheduled times
while True:
    schedule.run_pending()
    time.sleep(1)
