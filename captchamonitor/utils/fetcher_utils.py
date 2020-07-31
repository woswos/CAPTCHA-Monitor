import os
import signal
import logging
from selenium import webdriver


def force_quit_driver(driver):
    logger = logging.getLogger(__name__)

    pid = driver.service.process.pid

    # Close all windows
    for window in driver.window_handles:
        driver.switch_to.window(window)
        driver.close()

    # Quit the driver
    driver.quit()

    # Kill the process, just in case
    try:
        os.kill(int(pid), signal.SIGTERM)
        logger.debug("Force killed the process")

    except ProcessLookupError as ex:
        pass
