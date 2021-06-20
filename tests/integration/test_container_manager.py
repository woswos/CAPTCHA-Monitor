import unittest

from captchamonitor.utils.config import Config
from captchamonitor.utils.container_manager import ContainerManager


class TestContainerManager(unittest.TestCase):
    def setUp(self):
        self.config = Config()
        self.container_host = self.config["docker_firefox_browser_container_name"]

    def test_container_manager_init(self):
        container_manager = ContainerManager(self.container_host)

        self.assertEqual(container_manager.container_name, self.container_host)
        self.assertIsNotNone(container_manager.container_id)
