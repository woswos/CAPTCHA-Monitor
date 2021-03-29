import logging
from sqlalchemy import Column, Integer, String
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import database_exists, create_database
from captchamonitor.utils.exceptions import DatabaseInitError


class Database:
    """
    Communicates with the database using SQLAlchemy
    """

    def __init__(self, host, port, db_name, user, password):
        """
        Prepares the database connection and tables in the database

        :param host: Database host
        :type host: str
        :param port: Database port
        :type port: str
        :param db_name: Database name
        :type db_name: str
        :param user: Database user
        :type user: str
        :param password: Database password
        :type password: str
        """
        self.logger = logging.getLogger(__name__)

        self.connection_string = (
            f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}"
        )

        self.engine = create_engine(self.connection_string, echo=True)

        try:
            if not database_exists(self.engine.url):
                self.logger.info("Database doesn't exist, now creating it now")
                create_database(self.engine.url)
            else:
                self.logger.info("Database exists, skipping creation")

        except Exception as e:
            self.logger.warning("Could not connect to the database:\n %s", e)
            raise DatabaseInitError
