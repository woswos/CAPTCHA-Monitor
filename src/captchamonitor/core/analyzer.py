import logging

from sqlalchemy.orm import sessionmaker

from captchamonitor.utils.config import Config
from captchamonitor.utils.models import Domain, Fetcher, FetchCompleted


class Analyzer:
    """
    Analyses completed jobs
    """

    def __init__(
        self,
        analyzer_id: str,
        config: Config,
        db_session: sessionmaker,
    ) -> None:
        """
        Initializes a new analyser

        :param analyzer_id: Analyser ID assigned for this analyser
        :type analyzer_id: str
        :param config: The config class instance that contains global configuration values
        :type config: Config
        :param db_session: Database session used to connect to the database
        :type db_session: sessionmaker
        """
        # Private class attributes for analyser
        self.__logger = logging.getLogger(__name__)
        self.__config: Config = config
        self.__db_session: sessionmaker = db_session
        self.__analyzer_id: str = analyzer_id

        self.__loop_over_domains()

    def __loop_over_domains(self) -> None:
        """
        Loop over the domain list and get corresponding website data from the database
        """
        # pylint: disable=C0121,W0104
        domains = self.__db_session.query(Domain).all()

        for domain in domains:
            query_by_domain = (
                self.__db_session.query(FetchCompleted)
                .join(Fetcher)
                .filter(FetchCompleted.ref_domain == domain)
            )

            tor = query_by_domain.filter(Fetcher.uses_tor == True).first()
            non_tor = query_by_domain.filter(Fetcher.uses_tor == False).first()
            exit_relay = tor.ref_relay

            # Use the data for analysis
            tor.html_data
            tor.http_requests

            non_tor.html_data
            non_tor.http_requests

            exit_relay.fingerprint
