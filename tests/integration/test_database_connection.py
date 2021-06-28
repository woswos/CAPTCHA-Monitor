import pytest

from captchamonitor.utils.database import Database
from captchamonitor.utils.exceptions import DatabaseInitError


class TestDatabaseConnection:
    def test_connection_with_correct_credentials(self, config):
        Database(
            config["db_host"],
            config["db_port"],
            config["db_name"],
            config["db_user"],
            config["db_password"],
        )

    def test_connection_with_wrong_credentials(self):
        with pytest.raises(DatabaseInitError):
            Database("db_host", 1231, "db_name", "db_user", "db_password")
