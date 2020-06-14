import pytest
import logging
import captchamonitor.utils.tor_launcher as tor_launcher

logger_format = '%(asctime)s %(module)s [%(levelname)s] %(message)s'
logging.basicConfig(format=logger_format)
logger = logging.getLogger('captchamonitor')
logger.setLevel(logging.DEBUG)
logger = logging.getLogger('stem')
logger.setLevel(logging.INFO)
logger = logging.getLogger('log')
logger.setLevel(logging.INFO)



@pytest.fixture(scope="session", autouse=True)
def run_and_stop_tors():
    # Just to make sure that the descriptors are already downloaded
    tor = tor_launcher.TorLauncher()
    tor.start()
    tor.new_circuit()
    tor.stop()
