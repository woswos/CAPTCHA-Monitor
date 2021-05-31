import logging
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database
from captchamonitor.utils.models import Model
from captchamonitor.utils.exceptions import DatabaseInitError


class Database:
    """
    Communicates with the database using SQLAlchemy
    """

    def __init__(
        self,
        host: str,
        port: str,
        db_name: str,
        user: str,
        password: str,
        verbose: Optional[bool] = False,
    ) -> None:
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
        :param verbose: Print the generated SQL queries or not, defaults to False
        :type verbose: bool, optional
        """
        self.logger = logging.getLogger(__name__)

        self.connection_string = (
            f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}"
        )

        try:
            self.engine = create_engine(self.connection_string, echo=verbose)

            if not database_exists(self.engine.url):
                self.logger.info("Database doesn't exist, creating it now")
                create_database(self.engine.url)
            else:
                self.logger.info("Database exists, skipping creation")

        except Exception as exception:
            self.logger.warning("Could not connect to the database:\n %s", exception)
            raise DatabaseInitError from exception

        self.model = Model

        # Process models
        self.model.metadata.create_all(self.engine)

        # Create session
        self.session = sessionmaker(bind=self.engine)
