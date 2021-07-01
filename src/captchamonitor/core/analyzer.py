import json
import time
import logging
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup
from sqlalchemy.orm import sessionmaker

from captchamonitor.utils.config import Config
from captchamonitor.utils.models import (
    Domain,
    Fetcher,
    FetchCompleted,
    AnalyzeCompleted,
)


class Analyzer:
    """
    Analyzes completed jobs
    """

    def __init__(
        self,
        analyzer_id: str,
        config: Config,
        db_session: sessionmaker,
        loop: Optional[bool] = True,
    ) -> None:
        """
        Initializes a new analyzer

        :param analyzer_id: analyzer ID assigned for this analyzer
        :type analyzer_id: str
        :param config: The config class instance that contains global configuration values
        :type config: Config
        :param db_session: Database session used to connect to the database
        :type db_session: sessionmaker
        :param loop: Should I process a batch of domains or keep looping, defaults to True
        :type loop: bool, optional
        """
        # Public class attributes
        self.soup_t: BeautifulSoup = BeautifulSoup("", "html.parser")
        self.soup_n: BeautifulSoup = BeautifulSoup("", "html.parser")
        self.max_k: int = 150
        self.min_k: int = 20
        self.match_list: List[str] = [
            "error",
            "forbidden",
            "tor",
            "denied",
            "sorry",
        ]
        self.tor_store: Dict[str, Any] = {}
        self.non_store: Dict[str, Any] = {}
        self.captcha_checker_value: Optional[int] = None
        self.dom_analyze_value: Optional[int] = None
        self.status_check_value: Optional[int] = None

        # Private class attributes
        self.__logger = logging.getLogger(__name__)
        self.__config: Config = config
        self.__db_session: sessionmaker = db_session
        self.__analyzer_id: str = analyzer_id  # pylint: disable=W0238
        self.__job_queue_delay: float = float(self.__config["job_queue_delay"])

        # Loop over the jobs
        while loop:
            self.process_next_batch_of_domains()
            time.sleep(self.__job_queue_delay)

    def process_next_batch_of_domains(self) -> None:
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

            tor = query_by_domain.filter(Fetcher.uses_proxy_type == "tor").first()
            non_tor = query_by_domain.filter(Fetcher.uses_proxy_type == None).first()

            if tor is not None and non_tor is not None:

                # Loads JSON
                HAR_json_tor = json.loads(tor.http_requests)
                HAR_json_non_tor = json.loads(non_tor.http_requests)

                self.status_check(
                    tor.html_data,
                    HAR_json_tor,
                    non_tor.html_data,
                    HAR_json_non_tor,
                )

                # Non tor from the FetchCompleted
                analyzer_val_nt = AnalyzeCompleted(
                    captcha_checker=self.captcha_checker_value,
                    status_check=self.status_check_value,
                    dom_analyze=self.dom_analyze_value,
                    fetch_completed_id=non_tor.id,
                )
                # Tor from the FetchCompleted
                analyzer_val_t = AnalyzeCompleted(
                    captcha_checker=self.captcha_checker_value,
                    status_check=self.status_check_value,
                    dom_analyze=self.dom_analyze_value,
                    fetch_completed_id=tor.id,
                )
                self.__db_session.add(analyzer_val_nt)
                self.__db_session.add(analyzer_val_t)
                self.__db_session.commit()

    def captcha_checker(self) -> bool:
        """
        Two ways of checking captcha would be:
        1. Check if the HTML consists of Captcha or not for tor and non tor
        2. HAR contains captcha or not

        :return: Chech if captcha is returned or not
        :rtype: bool
        """
        # Assuming no captcha
        tor_c = 0
        tor = 0
        # If captcha in html of tor:
        if "captcha" in self.soup_t and "captcha" not in self.soup_n:
            tor_c = 1
        # If captcha in both, tor_html and non_tor html, or not anywhere:
        else:
            for s_ in self.tor_store:
                if "captcha" in s_:
                    tor = 1
                    self.__logger.info("Captcha in tor from HAR")
            for s_ in self.non_store:
                if "captcha" in s_:
                    tor = 0
                    self.__logger.info("Captcha in Non-Tor too")
        if tor == 0 and tor_c == 0:
            self.__logger.info("Same...")
            self.captcha_checker_value = 0
        else:
            self.__logger.info("Captcha Present")
            self.captcha_checker_value = 1
            return True
        return False

    # pylint:disable=R0912
    def dom_analyze(self, tor_html_data: str, non_tor_html_data: str) -> None:
        """
        Analyzes dom

        :param tor_html_data: Tor HTML data
        :type tor_html_data: str
        :param non_tor_html_data: Non-Tor HTML data
        :type non_tor_html_data: str
        """
        self.soup_t = BeautifulSoup(tor_html_data, "html.parser")
        count_t = 0
        node_tor = []
        node_non_tor = []

        for tag in self.soup_t.find_all(True):
            node_tor.append(tag)
            count_t += 1

        self.soup_n = BeautifulSoup(non_tor_html_data, "html.parser")

        count_n = 0
        for tag in self.soup_n.find_all(True):
            node_non_tor.append(tag)
            count_n += 1

        self.__logger.info("Nodes by tor: %s and non-tor: %s ", count_t, count_n)
        try:
            dom_score = 100 * ((count_n - count_t) / count_t)
        except ZeroDivisionError as e:
            self.__logger.info("Zero Error, check tor Dom: %s", e)

        self.__logger.info("DOM Score : %s", dom_score)

        self.soup_t = str(self.soup_t).lower()
        self.soup_n = str(self.soup_n).lower()

        if self.captcha_checker() is False:
            if abs(dom_score) > 0:
                if abs(dom_score) > self.max_k:
                    #   Random value to check the performance.
                    #   Might need some more experiments to come back with the correct value
                    #   or it hasn't been loaded fully (increase loading time)")
                    self.__logger.info("Tor most probably Errors!!")
                    self.dom_analyze_value = 0
                elif abs(dom_score) < self.min_k:
                    #   Random value to check the performance.
                    #   Might need some more experiments to come back with the correct value
                    #   checks for keywords to help in this case
                    self.__logger.info("Resembles same")
                    self.dom_analyze_value = 1
                else:
                    self.__logger.info("Doubtful case!!")
                    self.__logger.info("checking for keywords...")
                    #   checks for keywords to help in this case
                    res = 0
                    for _ in self.match_list:
                        if _ in self.soup_t and _ not in self.soup_n:
                            res = 1
                    if res == 0:
                        self.__logger.info("Same!!")
                        self.dom_analyze_value = 2
                    else:
                        self.__logger.info("Tor Blocked : checklist!! ")
                        self.dom_analyze_value = 3
            else:
                self.__logger.info("Same Resemblance")
                self.dom_analyze_value = 4

    def status_check(
        self,
        tor_html_data: str,
        tor_http_requests: Dict[str, Any],
        non_tor_html_data: str,
        non_tor_http_requests: Dict[str, Any],
    ) -> None:

        """
        HTTP Status code Checker

        :param tor_html_data: Tor HTML data
        :type tor_html_data: str
        :param tor_http_requests: Tor HAR
        :type tor_http_requests: Dict[str, Any]
        :param non_tor_html_data: Non-Tor HTML data
        :type non_tor_html_data: str
        :param non_tor_http_requests: Non-Tor HAR
        :type non_tor_http_requests: Dict[str, Any]
        """
        tor_H = {}
        tor_N = {}

        for i in range(0, len(tor_http_requests["log"]["entries"])):
            tor_H[
                tor_http_requests["log"]["entries"][i]["request"]["url"]
            ] = tor_http_requests["log"]["entries"][i]["response"]["status"]

        # pylint: disable=C0206
        for i in tor_H:
            if tor_H[i] != 0 or tor_H != "" or tor_H is not None:
                self.tor_store[i] = tor_H[i]  # type: ignore

        for i in range(len(non_tor_http_requests["log"]["entries"])):
            tor_N[
                non_tor_http_requests["log"]["entries"][i]["request"]["url"]
            ] = non_tor_http_requests["log"]["entries"][i]["response"]["status"]

        # pylint: disable=C0206
        for i in tor_N:
            if tor_N[i] != 0 or tor_N != "" or tor_N is not None:
                self.non_store[i] = tor_N[i]  # type: ignore

        first_url_t = list(self.tor_store.keys())[0]
        first_status_t = self.tor_store[str(first_url_t)]

        # non tor use HARExportTrigger
        first_url_nt = list(self.non_store.keys())[0]
        first_status_nt = self.non_store[str(first_url_nt)]

        if int(first_status_t) > 399 and int(first_status_nt) < 400:
            # Error for tag and no error for non tor
            self.__logger.info("Tor Blocked")
            self.status_check_value = 0

        elif int(first_status_t) > 399 and int(first_status_nt) > 399:
            # Both blocked on tor and non-tor
            self.__logger.info("Site is blocked on tor and non-tor browsers")
            self.status_check_value = 1

        elif int(first_status_t) < 300 and int(first_status_nt) > 399:
            # When tor isn't blocked and non-tor is blocked
            self.__logger.info("Tor is not blocked, rather non-tor browser is blocked")
            self.status_check_value = 2
        else:
            if int(first_status_t) > 299 and int(first_status_t) < 400:
                # Chek if tor returns error pages or warning or captchas due to reload
                self.dom_analyze(tor_html_data, non_tor_html_data)

            elif int(first_status_t) < 300 and int(first_status_nt) < 300:
                # When both tor and non tor returns no errors
                self.dom_analyze(tor_html_data, non_tor_html_data)
