import os
import shutil
import logging
from typing import Any, List, Tuple, Optional

import matplotlib.pyplot as plt
from jinja2 import Environment, FileSystemLoader
from sqlalchemy import Date, or_, cast
from sqlalchemy.orm import sessionmaker

from captchamonitor.utils.config import Config
from captchamonitor.utils.models import Relay, Domain, FetchCompleted, AnalyzeCompleted


class RenderDashboard:
    """
    Renders the latest version of the dashboard and exports the HTML files to
    www folder
    """

    def __init__(self, config: Config, db_session: sessionmaker) -> None:
        """
        Initializes the dashboard renderer

        :param config: The config class instance that contains global configuration values
        :type config: Config
        :param db_session: Database session used to connect to the database
        :type db_session: sessionmaker
        """
        # Private class attributes
        self.__logger = logging.getLogger(__name__)
        self.__config: Config = config
        self.__db_session: sessionmaker = db_session
        self.__template_location: str = os.path.join(
            self.__config["dashboard_location"], "templates"
        )
        self.__jinja_environment = Environment(
            loader=FileSystemLoader(self.__template_location)
        )
        self.graph_name: List[str] = []
        self.graph_string: Optional[Any] = []
        # Clean the www directory
        self.cleanup_www_folder()
        # Get hold of the docstrings
        self.graph_string.append(self.graph_for_tor_block.__doc__)
        self.graph_string.append(self.graph_for_tor_partial_block.__doc__)
        self.graph_string.append(self.graph_for_both_block.__doc__)
        self.graph_string.append(self.graph_for_tor_none_block.__doc__)
        # Render all pages
        self.render_index()
        self.render_domain_list()
        # Render graph: blocked websites for Tor
        self.graph_for_tor_block()
        # Render graph: partially blocked websites for Tor
        self.graph_for_tor_partial_block()
        # Render graph: blocked websites for both Tor and non-Tor nodes
        self.graph_for_both_block()
        # Render graph: accessible websites for Tor
        self.graph_for_tor_none_block()
        # Export graph to the website
        self.export_graph()

    def __write_to_file(self, filename: str, html_data: str) -> None:
        """
        Writes given data to the specified file inside the www folder

        :param filename: Name of the HTML file to export
        :type filename: str
        :param html_data: HTML data to write to the file
        :type html_data: str
        """
        html_file_path = os.path.join(self.__config["dashboard_www_location"], filename)
        with open(html_file_path, "w") as file:
            file.write(html_data)

    def cleanup_www_folder(self) -> None:
        """
        Remove contents of the www folder and copy the static folder again
        """
        self.__logger.debug("Cleaning up the www folder")

        www_location = self.__config["dashboard_www_location"]
        static_location = os.path.join(self.__config["dashboard_location"], "static")

        # Remove folders and files inside the www folder
        for filename in os.listdir(www_location):
            file_path = os.path.join(www_location, filename)
            if (os.path.isfile(file_path) or os.path.islink(file_path)) and (
                filename != ".gitignore"
            ):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)

        # Copy static files
        shutil.copytree(static_location, www_location, dirs_exist_ok=True)

    def render_index(self, filename: str = "index.html") -> None:
        """
        Render the index page, which visitors first see

        :param filename: Name of the HTML file to export, defaults to "index.html"
        :type filename: str
        """
        self.__logger.debug("Rendering %s", filename)

        template = self.__jinja_environment.get_template("index.html")
        html_data = template.render()

        self.__write_to_file(filename=filename, html_data=html_data)

    def render_domain_list(self, filename: str = "domain_list.html") -> None:
        """
        Render the page that contains the list of tracked domains

        :param filename: Name of the HTML file to export, defaults to "domain_list.html"
        :type filename: str
        """
        self.__logger.debug("Rendering %s", filename)

        data = self.__db_session.query(Domain).all()

        template = self.__jinja_environment.get_template("domain_list.html")
        html_data = template.render(data=data)

        self.__write_to_file(filename=filename, html_data=html_data)

    def render_graph(
        self,
        data_for_graph: List[List[Any]],
        ylabel: str,
        title: str,
        graph_type: str,
        color: str,
    ) -> None:
        """
        Renders the graph view.

        :param data_for_graph: Contains the data for the graph to be generated.Like: Scores for y axis, Timestamps for x axis, Total query, Obtained Query, Relay Fingerprint"
        :type data_for_graph: List[List[Any]]
        :param ylabel: Contains the label to be put in y-axis
        :type ylabel: str
        :param title: The Title of the Graph
        :type title: str
        :param graph_type: The type of the graph which is generated. Also put to differentiate from other graph names
        :type graph_type: str
        :param color: The color of the graph
        :type color: str
        """
        fig = plt.figure(figsize=(20, 10))  # pylint: disable=W0612
        plt.ylim(top=100)
        plt.bar(data_for_graph[1], data_for_graph[0], width=0.25, color=color)
        plt.xlabel("Timestamp in days")

        plt.ylabel(ylabel)
        plt.title(title)
        txt_str = f"No of websites that has been evaluated: {data_for_graph[3][2]}"
        plt.figtext(0.02, 0.035, txt_str)
        txt_str = f"total websites: {data_for_graph[2][2]}"
        plt.figtext(0.02, 0.005, txt_str)

        images_location = os.path.join(
            self.__config["dashboard_location"], "static/images/"
        )
        plt.savefig(images_location + f"relay_{data_for_graph[-1]}_{graph_type}.png")
        self.graph_name.append(f"relay_{data_for_graph[-1]}_{graph_type}.png")

    # pylint: disable=R0914
    def prepare_data_for_graph(self, filters: List[Any]) -> List[List[Any]]:
        """
        Synthesize Data for different graphs.

        :param filters: Contains the details of filters according to which the data is filtered
        :type filters: List[Any]
        :return: List of data to generate the graph. Like Scores for y axis, Timestamps for x axis, Total query, Obtained Query, Relay Fingerprint
        """
        self.__logger.debug("Prepare data for different graphs")
        analyze_db_data = self.__db_session.query(AnalyzeCompleted).all()
        timestamp_store = set()

        data_for_graph: List[List[Any]] = []
        sc = []
        dt = []
        total_job_query = []
        total_query = []
        time: Tuple[int, str] = (0, "")
        for _ in analyze_db_data:
            timestamp_store.add(
                f"{_.created_at.year}-{_.created_at.month}-{_.created_at.day}"
            )

        timestamp_list = sorted(list(timestamp_store))
        self.__logger.info(timestamp_list)

        # Gets hold of all relays
        relay_db_data = self.__db_session.query(Relay).all()

        for _ in relay_db_data:
            fetch_relay = (
                self.__db_session.query(FetchCompleted).filter(
                    FetchCompleted.relay_id == _.id  # pylint: disable=W0143
                )
            ).all()

            fetch_ids = []

            # Relays which are Fetched successfully
            for y in fetch_relay:
                fetch_ids.append(y.id)

            relay_fingerprint = _.fingerprint

            for time in enumerate(timestamp_list):
                total_query_ = (
                    self.__db_session.query(AnalyzeCompleted)
                    .filter(
                        cast(AnalyzeCompleted.created_at, Date)
                        >= f"{time[1]} 00:00:00",
                        cast(AnalyzeCompleted.created_at, Date)
                        <= f"{time[1]} 23:59:59",
                        AnalyzeCompleted.fetch_completed_id.in_(
                            fetch_ids
                        ),  # pylint: disable=E1101
                    )
                    .all()
                )
                # pylint: disable=E1101
                job_query = (
                    self.__db_session.query(AnalyzeCompleted)
                    .filter(
                        cast(AnalyzeCompleted.created_at, Date)
                        >= f"{time[1]} 00:00:00",
                        cast(AnalyzeCompleted.created_at, Date)
                        <= f"{time[1]} 23:59:59",
                        AnalyzeCompleted.fetch_completed_id.in_(fetch_ids),
                    )
                    .filter(or_(*filters))
                    .all()
                )

                count_total_query = len(total_query_)
                count_job_query = len(job_query)

                if count_total_query == 0:
                    break
                score = count_job_query / count_total_query * 100

                self.__logger.info(score)
                sc.append(score)
                dt.append(time[1])
                total_query.append(count_total_query)
                total_job_query.append(count_job_query)

        data_for_graph.append(sc)
        data_for_graph.append(dt)
        data_for_graph.append(total_query)
        data_for_graph.append(total_job_query)
        data_for_graph.append(relay_fingerprint)

        return data_for_graph

    def graph_for_tor_block(self) -> None:
        """
        Basic plot for the percentage of websites blocking the given Tor exit relay.
        """
        data_for_graph = self.prepare_data_for_graph(
            filters=[AnalyzeCompleted.status_check == 0]
        )
        title = f"Graph for relay ids: Fetches the websites using relay: {data_for_graph[4]}, \n and checks the percentage of blocked websites"
        ylabel = "Percentage where Tor is blocked (status_check) (%)"
        self.__logger.debug(data_for_graph)
        self.render_graph(
            data_for_graph, ylabel, title, graph_type="tor_blocked", color="maroon"
        )

    def graph_for_tor_partial_block(self) -> None:
        """
        Basic graph for the percentage of websites partially blocking tor for the given Tor exit relay.
        """
        data_for_graph = self.prepare_data_for_graph(
            filters=[AnalyzeCompleted.dom_analyze == 0]
        )
        title = f"Graph for relay ids: Fetches the websites using relay: {data_for_graph[4]}, \n and checks the percentage of websites partially blocking tor nodes"
        ylabel = "Percentage where Tor partially-blocked percentage (dom_analyze) (%)"
        self.__logger.debug(data_for_graph)
        self.render_graph(
            data_for_graph,
            ylabel,
            title,
            graph_type="partially_blocked",
            color="orange",
        )

    def graph_for_both_block(self) -> None:
        """
        Contains the basic graph for the percentage of websites blocking both Tor and Control Nodes
        """
        data_for_graph = self.prepare_data_for_graph(
            filters=[AnalyzeCompleted.status_check == 1]
        )
        title = f"Graph for relay ids: Fetches the websites using relay: {data_for_graph[4]}, \n and checks the percentage of websites blocking both the control nodes and tor nodes"
        ylabel = "Percentage where Both control nodes and tor blocked  percentage (status_check) (%)"
        self.__logger.debug(data_for_graph)
        self.render_graph(
            data_for_graph, ylabel, title, graph_type="both_blocked", color="yellow"
        )

    def graph_for_tor_none_block(self) -> None:
        """
        Contains the basic graph for the percentage of websites that let's Tor exit relay access them.
        """
        data_for_graph = self.prepare_data_for_graph(
            filters=[
                AnalyzeCompleted.dom_analyze == 1,
                AnalyzeCompleted.dom_analyze == 4,
            ]
        )
        title = f"Graph for relay ids: Fetches the websites using relay: {data_for_graph[4]}, \n and checks the percentage of websites unblocked by Tor"
        ylabel = "Percentage where Websites are unblocked by Tor (%)"
        self.__logger.debug(data_for_graph)
        self.render_graph(
            data_for_graph, ylabel, title, graph_type="none_blocked", color="green"
        )

    def export_graph(self, filename: str = "reanalyze.html") -> None:
        """
        Exports the graphs to the html file

        :param filename: Name of the HTML file to export, defaults to "reanalyze.html"
        :type filename: str
        """
        template = self.__jinja_environment.get_template("reanalyze.html")
        html_data = template.render(data=self.graph_name, string=self.graph_string)

        self.__write_to_file(filename=filename, html_data=html_data)
