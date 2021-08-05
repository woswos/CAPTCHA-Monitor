import sys
import json
import time
import logging
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup
from sqlalchemy import func
from sqlalchemy.orm import sessionmaker

from captchamonitor.utils.config import Config
from captchamonitor.utils.models import (
    Domain,
    Fetcher,
    MetaData,
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
        # Private class attributes
        self.__logger = logging.getLogger(__name__)
        self.__config: Config = config
        self.__db_session: sessionmaker = db_session
        self.__analyzer_id: str = analyzer_id  # pylint: disable=W0238
        self.__job_queue_delay: float = float(self.__config["job_queue_delay"])

        # Public class attributes
        self.soup_tor: BeautifulSoup = BeautifulSoup("", "html.parser")
        self.soup_non_tor: BeautifulSoup = BeautifulSoup("", "html.parser")
        self.max_threshold_value: int = 150
        self.min_threshold_value: int = 20
        self.match_list: List[str] = (
            self.__db_session.query(MetaData)
            .filter(MetaData.key == "analyzer_match_list")
            .one()
            .value
        )
        self.tor_store: Dict[str, Any] = {}
        self.non_store: Dict[str, Any] = {}
        self.captcha_checker_value: Optional[int] = None
        self.dom_analyze_value: Optional[int] = None
        self.status_check_value: Optional[int] = None
        self.consensus_lite_dom_value: Optional[int] = None
        self.captcha_proxy_val: List[int]
        self.consensus_lite_captcha_value: Optional[int] = None

        # Loop over the jobs
        while loop:
            self.process_next_batch_of_domains()
            time.sleep(self.__job_queue_delay)

    # pylint: disable=R0914
    def process_next_batch_of_domains(self) -> None:
        """
        Loop over the domain list and get corresponding website data from the database
        """
        # pylint: disable=C0121,W0104
        domains = self.__db_session.query(Domain)
        for domain in domains:
            query_by_domain = (
                self.__db_session.query(FetchCompleted)
                .join(Fetcher)
                .filter(FetchCompleted.ref_domain == domain)
            )

            tor = query_by_domain.filter(Fetcher.uses_proxy_type == "tor").first()
            non_tor = query_by_domain.filter(Fetcher.uses_proxy_type == None).first()
            proxies = query_by_domain.filter(Fetcher.uses_proxy_type == "http").all()

            if tor is not None and non_tor is not None:
                proxy_countries_html_data = []
                for proxy in proxies:
                    if proxy.url == tor.url:
                        proxy_countries_html_data.append(proxy.html_data)

                # Loads JSON
                HAR_json_tor = json.loads(tor.http_requests)
                HAR_json_non_tor = json.loads(non_tor.http_requests)
                self.captcha_checker_value = None
                self.dom_analyze_value = None
                self.status_check_value = None
                self.consensus_lite_dom_value = None
                self.consensus_lite_captcha_value = None
                self.tor_store = {}
                self.non_store = {}

                self.status_check(
                    tor.html_data,
                    HAR_json_tor,
                    non_tor.html_data,
                    HAR_json_non_tor,
                    proxy_countries_html_data,
                )

                fetch_completed_present = (
                    self.__db_session.query(
                        func.count(AnalyzeCompleted.fetch_completed_id)
                    ).filter(
                        AnalyzeCompleted.fetch_completed_id  # pylint: disable=W0143
                        == tor.id
                    )
                ).all()
                if fetch_completed_present[0][0] == 0:
                    # Tor from the FetchCompleted
                    analyzer_val_t = AnalyzeCompleted(
                        captcha_checker=self.captcha_checker_value,
                        status_check=self.status_check_value,
                        dom_analyze=self.dom_analyze_value,
                        consensus_lite_dom=self.consensus_lite_dom_value,
                        consensus_lite_captcha=self.consensus_lite_captcha_value,
                        fetch_completed_id=tor.id,
                    )

                    self.__db_session.add(analyzer_val_t)
                    self.__db_session.commit()

    def consensus_lite_captcha(self) -> None:
        """
        Extension to the consensus lite module for captcha checking
        """
        # Every proxy list has captcha and similarly tor and non-tor doms have captcha:
        # Two cases:
        # 1. Either the website returns captcha everytime
        # 2. or, the website is about captcha itself.
        if 0 not in self.captcha_proxy_val and self.captcha_checker_value == 0:
            self.__logger.info("Captcha is prevalent in every case")
            self.consensus_lite_captcha_value = 1
        # Assume proxy list with captcha returned and not returned and either captcha returned in both nt and t, or not returned in both nt and t.
        # Case might be a bit rare.
        # Tracing it for further details
        elif 1 in self.captcha_proxy_val and self.captcha_checker_value == 0:
            self.__logger.info(
                "captcha in all or just in proxy, not much useful for us, because even if proxy is returned non-tor too is targeted with proxy"
            )
            self.consensus_lite_captcha_value = 2
        # No captcha case
        elif 1 not in self.captcha_proxy_val and self.captcha_checker_value == 0:
            self.__logger.info("No captcha for this website")
            self.consensus_lite_captcha_value = 3
        # Only non-tor returns no captcha
        elif 0 not in self.captcha_proxy_val and self.captcha_checker_value == 1:
            self.__logger.info("Proxy and Tor returns captcha")
            self.consensus_lite_captcha_value = 4
        # Proxy might have/haven't captcha, but tor has
        elif 0 in self.captcha_proxy_val and self.captcha_checker_value == 1:
            self.__logger.info("Tor returns captcha")
            self.consensus_lite_captcha_value = 5
        # Only tor has captcha, might be the case when len(self.captcha_proxy_val) is small too
        elif 1 not in self.captcha_proxy_val and self.captcha_checker_value == 1:
            self.__logger.info("Partiality towards just tor")
            self.consensus_lite_captcha_value = 6

    def consensus_lite_dom(
        self, tor_dom: int, non_tor_dom: int, proxy_dom: List[int]
    ) -> None:
        """
        Consensus Lite Module for the dom checker

        :param tor_dom: Tor HTML dom nodes
        :type tor_dom: int
        :param non_tor_dom: Non-Tor HTML dom nodes
        :type non_tor_dom: int
        :param proxy_dom: List of Proxy dom nodes
        :type proxy_dom: List[int]
        """
        mn_difference_nt_and_t = abs(tor_dom - non_tor_dom)
        mn_difference_nt_and_proxy = int(sys.float_info.max)
        sum_proxy = 0

        if len(proxy_dom) > 0 and tor_dom > 0 and non_tor_dom > 0:
            for dom in proxy_dom:
                sum_proxy = sum_proxy + dom
                # Check for the minimum difference between non-tor and proxy
                mn_difference_nt_and_proxy = min(
                    mn_difference_nt_and_proxy, abs(dom - non_tor_dom)
                )
                # If Dom of proxy is greater than non-tor, place a flag for later operations.
                if dom > non_tor_dom:
                    neg_pos_var = -1
                else:
                    neg_pos_var = 1

            avg_proxy = sum_proxy / len(proxy_dom)

            score_proxy = neg_pos_var * (mn_difference_nt_and_proxy / non_tor_dom) * 100
            score_tor = (mn_difference_nt_and_t / non_tor_dom) * 100

            self.__logger.info(
                "Score Proxy: %f and Score tor: %f", score_proxy, score_tor
            )

            # Similar
            if (
                score_proxy < self.min_threshold_value
                and score_tor < self.min_threshold_value
            ):
                self.__logger.info("Not Blocked")
                self.consensus_lite_dom_value = 0

            # Tor Blocked
            elif (
                score_proxy < self.min_threshold_value
                and score_tor > self.min_threshold_value
            ):
                self.__logger.info("Tor Blocked")
                self.consensus_lite_dom_value = 1

            # Either Both Redirected to other page or both blocked
            elif (
                score_proxy > self.min_threshold_value
                and score_tor > self.min_threshold_value
            ):
                self.__logger.info("Both Redirected to other page or Both Blocked")
                self.consensus_lite_dom_value = 2

            # Proxy not good, Tor better
            elif (
                score_proxy > self.min_threshold_value
                and score_tor < self.min_threshold_value
            ):
                self.__logger.info("Tor unblocked, proxy blocked")
                self.consensus_lite_dom_value = 3

            # Website is in accessible by non-tor
            elif (
                score_proxy < 0
                and score_tor < 0
                and (100 * abs(avg_proxy - tor_dom)) / avg_proxy
                < self.min_threshold_value
            ):
                self.__logger.info("Non-Tor blocked")
                self.consensus_lite_dom_value = 4

            # No case have been thought of
            else:
                self.__logger.info("Case hasn't been thought of")
                self.consensus_lite_dom_value = 5

        self.consensus_lite_captcha()

    def captcha_checker(self) -> bool:
        """
        Two ways of checking captcha would be:
        1. Check if the HTML consists of Captcha or not for tor and non tor
        2. HAR contains captcha or not

        :return: Check if captcha is returned or not
        :rtype: bool
        """
        # Assuming no captcha
        tor_c = 0
        tor = 0
        # If captcha in html of tor:
        if "captcha" in self.soup_tor and "captcha" not in self.soup_non_tor:
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

    # pylint: disable=R0912,R0914,R0915
    def dom_analyze(
        self,
        tor_html_data: str,
        non_tor_html_data: str,
        proxy_countries_html_data: List[str],
    ) -> None:
        """
        Analyzes dom

        :param tor_html_data: Tor HTML data
        :type tor_html_data: str
        :param non_tor_html_data: Non-Tor HTML data
        :type non_tor_html_data: str
        :param proxy_countries_html_data: List of Proxy html data
        :type proxy_countries_html_data: List[str]
        """
        self.soup_tor = BeautifulSoup(tor_html_data, "html.parser")
        # Count the number of nodes in tor
        tor_node_count = len(self.soup_tor.find_all(True))

        self.soup_non_tor = BeautifulSoup(non_tor_html_data, "html.parser")
        # Count the number of nodes in non-tor
        non_tor_node_count = len(self.soup_non_tor.find_all(True))

        # Count the number of nodes returned by the proxies
        proxy_node_count = []
        proxy_node_detail = []
        self.captcha_proxy_val = []

        for proxy_html in proxy_countries_html_data:
            node_proxy = []
            soup_proxy = BeautifulSoup(proxy_html, "html.parser")
            # Check for captcha here itself, thereby reducing the space of the list ass well as execution later
            captcha_proxy = str(soup_proxy).lower()
            # Contains captcha or not in forms of 0(No captcha) and 1(Captcha), so that it can be accessed via another class
            self.captcha_proxy_val.append(int("captcha" in captcha_proxy))
            for tag in soup_proxy.find_all(True):
                node_proxy.append(tag)
            proxy_node_detail.append(node_proxy)
            proxy_node_count.append(len(node_proxy))

        self.__logger.info(
            "Nodes by tor: %f, non-tor: %f and proxies: %s",
            tor_node_count,
            non_tor_node_count,
            proxy_node_count,
        )
        try:
            dom_score = abs(
                100 * ((non_tor_node_count - tor_node_count) / tor_node_count)
            )
        except ZeroDivisionError as e:
            self.__logger.info("Zero Error, check tor Dom: %s", e)

        self.__logger.info("DOM Score : %s", dom_score)

        self.soup_tor = str(self.soup_tor).lower()
        self.soup_non_tor = str(self.soup_non_tor).lower()

        if self.captcha_checker() is False:
            if dom_score > 0:
                if dom_score > self.max_threshold_value:
                    # Random value to check the performance.
                    # Might need some more experiments to come back with the correct value
                    self.__logger.info("Tor most probably Errors!!")
                    self.dom_analyze_value = 0
                    # Call Consensus lite
                    self.consensus_lite_dom(
                        tor_node_count, non_tor_node_count, proxy_node_count
                    )
                elif dom_score < self.min_threshold_value:
                    # Random value to check the performance.
                    # Might need some more experiments to come back with the correct value
                    # Checks for keywords to help in this case
                    self.__logger.info("Resembles same")
                    self.dom_analyze_value = 1
                else:
                    self.__logger.info("Doubtful case!!")
                    self.__logger.info("checking for keywords...")
                    #   checks for keywords to help in this case
                    for _ in self.match_list:
                        if _ in self.soup_tor and _ not in self.soup_non_tor:
                            self.__logger.info("Tor Blocked : checklist!! ")
                            self.dom_analyze_value = 3
                        else:
                            self.__logger.info(
                                "Survived Checklist but still doubt (Further modules might help)"
                            )
                            self.dom_analyze_value = 2
                    # Call Consensus lite
                    self.consensus_lite_dom(
                        tor_node_count, non_tor_node_count, proxy_node_count
                    )
            else:
                # When DOM is equal
                self.__logger.info("Equal")
                self.dom_analyze_value = 4
            proxy_node_count = []

    def status_check(
        self,
        tor_html_data: str,
        tor_http_requests: Dict[str, Any],
        non_tor_html_data: str,
        non_tor_http_requests: Dict[str, Any],
        proxy_countries_html_data: List[str],
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
        :param proxy_countries_html_data: Html data of all given proxies matching the location of tor nodes.
        :type proxy_countries_html_data: List[str]
        """
        tor_HAR = {}
        non_tor_HAR = {}
        try:
            for i in range(0, len(tor_http_requests["log"]["entries"])):
                tor_HAR[
                    tor_http_requests["log"]["entries"][i]["request"]["url"]
                ] = tor_http_requests["log"]["entries"][i]["response"]["status"]
            # pylint: disable=C0206
            for i in tor_HAR:
                if tor_HAR[i] != 0 or tor_HAR != "" or tor_HAR is not None:
                    if 300 <= tor_HAR[i] < 400:
                        continue
                    self.tor_store[i] = tor_HAR[i]  # type: ignore
                    break

            for i in range(len(non_tor_http_requests["log"]["entries"])):
                non_tor_HAR[
                    non_tor_http_requests["log"]["entries"][i]["request"]["url"]
                ] = non_tor_http_requests["log"]["entries"][i]["response"]["status"]

            # pylint: disable=C0206
            for i in non_tor_HAR:
                if non_tor_HAR[i] != 0 or non_tor_HAR != "" or non_tor_HAR is not None:
                    if 300 <= non_tor_HAR[i] < 400:
                        continue
                    self.non_store[i] = non_tor_HAR[i]  # type: ignore
                    break

            first_url_t = list(self.tor_store.keys())[0]
            first_status_tor = int(self.tor_store[str(first_url_t)])

            # non tor use HARExportTrigger
            first_url_nt = list(self.non_store.keys())[0]
            first_status_non_tor = int(self.non_store[str(first_url_nt)])

            self.__logger.info(
                "Tor status: %d and Nontor status: %d",
                first_status_tor,
                first_status_non_tor,
            )

            if first_status_tor > 399 and first_status_non_tor < 400:
                # Error for tag and no error for non tor
                self.__logger.info("Tor Blocked")
                self.status_check_value = 0

            elif first_status_tor > 399 and first_status_non_tor > 399:
                # Both blocked on tor and non-tor
                self.__logger.info("Site is blocked on tor and non-tor browsers")
                self.status_check_value = 1

            elif first_status_tor < 300 and first_status_non_tor > 399:
                # When tor isn't blocked and non-tor is blocked
                self.__logger.info(
                    "Tor is not blocked, rather non-tor browser is blocked"
                )
                self.status_check_value = 2
            else:
                if (400 > first_status_tor > 299) or (
                    first_status_tor < 300 and first_status_non_tor < 300
                ):
                    # Check if tor returns error pages or warning or captchas due to reload
                    self.dom_analyze(
                        tor_html_data, non_tor_html_data, proxy_countries_html_data
                    )
        except TypeError:
            self.__logger.debug(
                "Check for the HARExport. Might have actually returned nothing"
            )
        except IndexError:
            self.__logger.debug(
                "Check for the HARExport. Might have no entries and is out of indexes"
            )
