import pytest
import unittest
from captchamonitor.utils.config import Config
from captchamonitor.utils.database import Database
from captchamonitor.utils.exceptions import DatabaseInitError


class TestDatabaseConnection(unittest.TestCase):
    def test_connection_with_correct_credentials(self):
        config = Config()
        Database(
            config["db_host"],
            config["db_port"],
            config["db_name"],
            config["db_user"],
            config["db_password"],
        )

    def test_connection_with_wrong_credentials(self):
        with pytest.raises(DatabaseInitError) as pytest_wrapped_e:
            Database("db_host", 1231, "db_name", "db_user", "db_password")

        # Check if the exception is correct
        self.assertEqual(pytest_wrapped_e.type, DatabaseInitError)
