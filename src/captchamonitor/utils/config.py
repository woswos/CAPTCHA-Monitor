import os
import logging
from typing import Any, KeysView, Optional, ValuesView

from captchamonitor.version import __version__
from captchamonitor.utils.exceptions import ConfigInitError

ENV_VARS = {
    "db_host": "CM_DB_HOST",
    "db_port": "CM_DB_PORT",
    "db_name": "CM_DB_NAME",
    "db_user": "CM_DB_USER",
    "db_password": "CM_DB_PASSWORD",
    "docker_network": "CM_DOCKER_NETWORK",
    "docker_tor_container_image": "CM_DOCKER_TOR_CONTAINER_IMAGE",
    "docker_tor_authentication_password": "CM_DOCKER_TOR_AUTH_PASS",
    "docker_tor_authentication_password_hashed": "CM_DOCKER_TOR_AUTH_PASS_HASHED",
    "docker_tor_browser_container_name": "CM_DOCKER_TOR_BROWSER_CONTAINER_NAME",
    "docker_tor_browser_container_port": "CM_DOCKER_TOR_BROWSER_CONTAINER_PORT",
    "docker_tor_browser_container_profile_location": "CM_DOCKER_TOR_BROWSER_CONTAINER_PROFILE_LOCATION",
    "docker_firefox_browser_container_name": "CM_DOCKER_FIREFOX_BROWSER_CONTAINER_NAME",
    "docker_firefox_browser_container_port": "CM_DOCKER_FIREFOX_BROWSER_CONTAINER_PORT",
    "docker_chrome_browser_container_name": "CM_DOCKER_CHROME_BROWSER_CONTAINER_NAME",
    "docker_chrome_browser_container_port": "CM_DOCKER_CHROME_BROWSER_CONTAINER_PORT",
    "docker_brave_browser_container_name": "CM_DOCKER_BRAVE_BROWSER_CONTAINER_NAME",
    "docker_brave_browser_container_port": "CM_DOCKER_BRAVE_BROWSER_CONTAINER_PORT",
    "docker_opera_browser_container_name": "CM_DOCKER_OPERA_BROWSER_CONTAINER_NAME",
    "docker_opera_browser_container_port": "CM_DOCKER_OPERA_BROWSER_CONTAINER_PORT",
    "asset_har_export_extension_xpi": "CM_ASSET_HAR_EXPORT_EXTENSION_XPI",
    "asset_har_export_extension_xpi_id": "CM_ASSET_HAR_EXPORT_EXTENSION_XPI_ID",
    "asset_har_export_extension_crx": "CM_ASSET_HAR_EXPORT_EXTENSION_CRX",
    "asset_gdpr_extension_xpi": "CM_ASSET_GDPR_EXTENSION_XPI",
    "asset_gdpr_extension_xpi_id": "CM_ASSET_GDPR_EXTENSION_XPI_ID",
    "asset_gdpr_extension_crx": "CM_ASSET_GDPR_EXTENSION_CRX",
    "job_queue_delay": "CM_JOB_QUEUE_DELAY",
    "fixture_location": "CM_FIXTURE_LOCATION",
    "dashboard_location": "CM_DASHBOARD_LOCATION",
    "dashboard_www_location": "CM_DASHBOARD_WWW_LOCATION",
}


class Config:
    """
    Behaves like a real python dictionary and also reads config variables from
    the environment

    Based on: https://gist.github.com/turicas/1510860
    """

    def __init__(self, init: Optional[dict] = None) -> None:
        # Add if initial values are passed
        if init is not None:
            self.__dict__.update(init)

        # Read environment variables
        for key, value in ENV_VARS.items():
            temp = os.environ.get(value, None)
            if temp is None:
                logging.getLogger(__name__).error(
                    "Missing configuration variable: %s", value
                )
                raise ConfigInitError
            self.__dict__[key] = temp

        # Add CAPTCHA Monitor version
        self.__dict__["version"] = __version__

    def __getitem__(self, key: Any) -> Any:
        try:
            return self.__dict__[key]
        except (KeyError, AttributeError) as exception:
            logging.getLogger(__name__).error(
                "Requested key doesn't exist in config: %s", key
            )
            raise exception

    def __setitem__(self, key: Any, value: Any) -> None:
        self.__dict__[key] = value

    def __delitem__(self, key: Any) -> None:
        del self.__dict__[key]

    def __contains__(self, key: Any) -> bool:
        return key in self.__dict__

    def __len__(self) -> int:
        return len(self.__dict__)

    def __repr__(self) -> Any:
        return repr(self.__dict__)

    def keys(self) -> KeysView[str]:
        return self.__dict__.keys()

    def values(self) -> ValuesView[Any]:
        return self.__dict__.values()
