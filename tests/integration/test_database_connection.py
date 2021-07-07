# pylint: disable=C0115,C0116,W0212

import pytest

from captchamonitor.utils.database import Database
from captchamonitor.utils.exceptions import DatabaseInitError


class TestDatabaseConnection:
    @staticmethod
    def test_connection_with_correct_credentials(config):
        Database(
            config["db_host"],
            config["db_port"],
            config["db_name"],
            config["db_user"],
            config["db_password"],
        )

    @staticmethod
    def test_connection_with_wrong_credentials():
        with pytest.raises(DatabaseInitError):
            Database("db_host", 1231, "db_name", "db_user", "db_password")
