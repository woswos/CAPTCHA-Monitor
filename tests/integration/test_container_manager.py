from captchamonitor.utils.container_manager import ContainerManager


class TestContainerManager:
    def test_container_manager_init(self, config):
        container_host = config["docker_firefox_browser_container_name"]

        container_manager = ContainerManager(container_host)

        assert container_manager.container_name == container_host
        assert container_manager.container_id is not None
