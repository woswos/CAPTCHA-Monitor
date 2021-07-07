# pylint: disable=C0115,C0116,W0212

from captchamonitor.utils.container_manager import ContainerManager


class TestContainerManager:
    @staticmethod
    def test_container_manager_init(config):
        container_host = config["docker_firefox_browser_container_name"]

        container_manager = ContainerManager(container_host)

        assert container_manager.container_name == container_host
        assert container_manager.container_id is not None
