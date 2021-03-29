import time
import logging
import schedule
from captchamonitor.cm import CaptchaMonitor


# Get the root logger for the package
logging.basicConfig(format="%(asctime)s %(module)s [%(levelname)s] %(message)s")
logger = logging.getLogger("captchamonitor")
logger.setLevel(logging.DEBUG)

# Create the CAPTCHA Monitor
logger.info("Intializing CAPTCHA Monitor")
cm = CaptchaMonitor()

# Schedule tasks
logger.info("Scheduling tasks")
schedule.every(3).seconds.do(cm.worker)

# Run jobs
logger.info("Started running the tasks")
while True:
    schedule.run_pending()
    time.sleep(1)
