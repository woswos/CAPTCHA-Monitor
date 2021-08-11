import os
import json
import shutil
import logging
from typing import Any, Set, Dict, List, Optional
from collections import defaultdict

import matplotlib.pyplot as plt
from jinja2 import Environment, FileSystemLoader
from sqlalchemy import func
from sqlalchemy.orm import sessionmaker

from captchamonitor.utils.config import Config
from captchamonitor.utils.models import Relay, Domain, FetchCompleted, AnalyzeCompleted


class Json:
    """
    Maps the Data into Json ready format
    """

    def __init__(self, rid: str, date_data: dict) -> None:
        """
        Structuring in JSON format

        :param rid: Entry for relay_id
        :type rid: str
        :param date_data: Entry for the analyzed data and dates
        :type date_data: dict
        """
        self.rid = rid
        self.date_data = date_data
        self.relay()

    def relay(self) -> Any:
        """
        Populates Relay with id and results
        :return: relay part of the JSON
        """
        d: Dict[str, Any] = {}
        d["id"] = self.rid
        d["result"] = self.result()
        return str(d).replace("'", '"')

    def result(self) -> List[Any]:
        """
        Populates the inner list of the Json
        :return: List of results (Date and Data)
        """
        list_res = []
        temp = {}
        # print(type(self.date_data))
        for i in self.date_data:
            # print(i,self.date_data[i])
            temp["date"] = i
            temp["data"] = self.date_data[i]

            list_res.append(temp)
            temp = {}
        return list_res


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
        # self.graph_name: List[str] = []
        self.graph_name: Dict[Any, List] = defaultdict(list)
        # self.global_fingerprint = []
        self.global_fingerprint: Set[str] = set()
        self.image_name: List[str] = []
        self.graph_string: Optional[Any] = []

        self.data_for_graph: Dict[Any, Any] = self.prepare_data_for_graph()
        # Clean the www directory
        self.cleanup_www_folder()
        # Get hold of the docstrings
        self.graph_string.append(self.graph_for_tor_block.__doc__)
        self.graph_string.append(self.graph_for_tor_partial_block.__doc__)
        self.graph_string.append(self.graph_for_both_block.__doc__)
        self.graph_string.append(self.graph_for_tor_none_block.__doc__)
        # Render all pages
        self.render_index()
        # self.render_dashboard()
        self.render_domain_list()
        # Render graph: blocked websites for Tor
        self.graph_for_tor_block()
        # Render graph: partially blocked websites for Tor
        self.graph_for_tor_partial_block()
        # # Render graph: blocked websites for both Tor and non-Tor nodes
        self.graph_for_both_block()
        # # Render graph: accessible websites for Tor
        self.graph_for_tor_none_block()
        # # Export graph to the website
        self.export_graph()
        self.render_dashboard()

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

    # pylint: disable=R0914
    def prepare_data_for_graph(self) -> Dict[Any, Any]:
        """
        Synthesize Data for different graphs.

        :return: JSON data to generate the graph. Like Scores for y axis, Timestamps for x axis, Total query, Obtained Query, Relay Fingerprint
        """
        data_point = (
            self.__db_session.query(
                func.count(AnalyzeCompleted.id),
                func.date(AnalyzeCompleted.created_at),
                FetchCompleted.relay_id,
            )
            .join(
                # pylint: disable=W0143
                FetchCompleted,
                AnalyzeCompleted.fetch_completed_id == FetchCompleted.id,
            )
            .group_by(func.date(AnalyzeCompleted.created_at))
            .group_by(FetchCompleted.relay_id)
            .order_by(FetchCompleted.relay_id)
            .order_by(func.date(AnalyzeCompleted.created_at))
            .all()
        )
        print("Data point: ", data_point)

        time: Any = []
        relay_id: List[str] = []
        relay_data_test: Dict[Any, Dict] = defaultdict(dict)

        for k, y in enumerate(data_point):
            tt = f"{y[1].year}-{y[1].month}-{y[1].day}"
            relay_id.append(y[2])
            if relay_data_test[relay_id[k]] == {}:
                uu: Dict[Any, List] = defaultdict(list)
            uu[tt] = []
            relay_data_test[relay_id[k]] = dict(uu)

        print("relay data test: ", dict(relay_data_test))

        fingerprint_set: Set[Any] = set()
        time_set: Set[Any] = set()
        for key, time in relay_data_test.items():
            print("Time in loop: ", time)
            fingerprint = (
                self.__db_session.query(Relay.fingerprint).filter(Relay.id == key).all()
            )
            fingerprint = fingerprint[0][0]
            for time_ in time.keys():
                # print("time_ variable: ", time_)
                work_data: List[Any] = []
                analyzed_data = (
                    self.__db_session.query(func.count(AnalyzeCompleted.id))
                    .join(
                        # pylint: disable=W0143
                        FetchCompleted,
                        AnalyzeCompleted.fetch_completed_id == FetchCompleted.id,
                    )
                    .filter(FetchCompleted.relay_id == key)  # pylint: disable=W0143
                    .filter(func.date(AnalyzeCompleted.created_at) == time_)
                    .all()
                )

                fingerprint_set.add(fingerprint)
                time_set.add(time_)

                # Test
                test_data = (
                    self.__db_session.query(func.count(AnalyzeCompleted.id))
                    .join(
                        FetchCompleted,
                        AnalyzeCompleted.fetch_completed_id  # pylint: disable=W0143
                        == FetchCompleted.id,
                    )
                    .filter(FetchCompleted.relay_id == key)  # pylint: disable=W0143
                    .filter(func.date(AnalyzeCompleted.created_at) == time_)
                    .filter(AnalyzeCompleted.status_check == 0)
                    .all()
                )

                tor_block = test_data[0][0]
                test_data = (
                    self.__db_session.query(func.count(AnalyzeCompleted.id))
                    .join(
                        FetchCompleted,
                        AnalyzeCompleted.fetch_completed_id  # pylint: disable=W0143
                        == FetchCompleted.id,
                    )
                    .filter(FetchCompleted.relay_id == key)  # pylint: disable=W0143
                    .filter(func.date(AnalyzeCompleted.created_at) == time_)
                    .filter(AnalyzeCompleted.status_check == 1)
                    .all()
                )

                all_block = test_data[0][0]

                test_data = (
                    self.__db_session.query(func.count(AnalyzeCompleted.id))
                    .join(
                        FetchCompleted,
                        AnalyzeCompleted.fetch_completed_id  # pylint: disable=W0143
                        == FetchCompleted.id,
                    )
                    .filter(FetchCompleted.relay_id == key)  # pylint: disable=W0143
                    .filter(func.date(AnalyzeCompleted.created_at) == time_)
                    .filter(AnalyzeCompleted.dom_analyze.in_([1, 4]))
                    .all()
                )
                all_work = test_data[0][0]

                test_data = (
                    self.__db_session.query(func.count(AnalyzeCompleted.id))
                    .join(
                        FetchCompleted,
                        AnalyzeCompleted.fetch_completed_id  # pylint: disable=W0143
                        == FetchCompleted.id,
                    )
                    .filter(FetchCompleted.relay_id == key)  # pylint: disable=W0143
                    .filter(func.date(AnalyzeCompleted.created_at) == time_)
                    .filter(AnalyzeCompleted.dom_analyze == 0)
                    .all()
                )
                partial_block = test_data[0][0]

                work_data.append(round(tor_block / analyzed_data[0][0] * 100, 2))
                work_data.append(round(partial_block / analyzed_data[0][0] * 100, 2))
                work_data.append(round(all_block / analyzed_data[0][0] * 100, 2))
                work_data.append(round(all_work / analyzed_data[0][0] * 100, 2))
                work_data.append(analyzed_data[0][0])

                relay_data_test[key][time_] = work_data  # pylint: disable=R1733

        print("relay data test: ", dict(relay_data_test))

        add = []
        y = tuple()
        for i in relay_data_test.keys():
            fingerprint = (
                self.__db_session.query(Relay.fingerprint).filter(Relay.id == i).all()
            )
            y = (fingerprint[0][0], i)
            add.append(y)

        print(add)
        for i in add:
            relay_data_test[i[0]] = relay_data_test.pop(i[1])

        concat_json = ""
        new_string = ""

        for key in relay_data_test:
            a = Json(rid=key, date_data=relay_data_test[key])
            concat_json += f"{(a.relay())},"
            new_string = f'"relay_id" : [{concat_json[:-1]}]'
            new_string = "{" + new_string + "}"

        return json.loads(new_string)

    def render_graph_new(
        self,
        kth: int,
        fingerprint: str,
        data_for_graph: Dict[Any, Any],
        ylabel: str,
        title: str,
        graph_type: int,
        color: str,
    ) -> None:
        """
        Renders the graph.

        :param kth: Gets the detail of K th Relay_id
        :type kth: int
        :param fingerprint: The fingerprint taken into consideration
        :type fingerprint: str
        :param data_for_graph: Details of all Relays with different timestamp and the analyzed data
        :type data_for_graph: (Dict[Any, Any])
        :param ylabel: ylabel for the Graph
        :type ylabel: str
        :param title: Title of the Graph
        :param graph_type: The type of graph one wants to associate the plot with (Block, partial block, all block, none blocked)
        :type graph_type: int
        :param color: color for the graph to be generated
        :type color: str
        """
        time = []
        data = []
        websites = 0
        x = len(data_for_graph["relay_id"][kth]["result"])
        for i in range(x):
            # x axis
            time.append(data_for_graph["relay_id"][kth]["result"][i]["date"])
            data.append(
                data_for_graph["relay_id"][kth]["result"][i]["data"][graph_type]
            )
            websites += data_for_graph["relay_id"][kth]["result"][i]["data"][4]

        fig = plt.figure(figsize=(20, 10))  # pylint: disable=W0612
        plt.ylim(top=100)
        plt.bar(time, data, width=0.25, color=color)
        plt.xlabel("Timestamp in days")

        plt.ylabel(ylabel)
        plt.title(title)
        txt_str = f"No of websites that has been evaluated: {websites/x}"
        plt.figtext(0.02, 0.035, txt_str)
        plt.rcParams.update({"font.size": 20})
        plt.rc("xtick", labelsize=26)
        plt.rc("ytick", labelsize=26)

        images_location = os.path.join(
            self.__config["dashboard_location"], "static/images/"
        )
        plt.savefig(images_location + f"relay_{fingerprint}_{graph_type}.png")
        self.graph_name[fingerprint].append(f"relay_{fingerprint}_{graph_type}.png")
        plt.close()

    def graph_for_tor_block(self) -> None:
        """
        Basic plot for the percentage of websites blocking the given Tor exit relay.
        """
        title = "Checks the percentage of blocked websites"
        ylabel = "Percentage where Tor is blocked (status_check) (%)"
        length = len(self.data_for_graph["relay_id"])
        for i in range(0, length):
            fingerprint = self.data_for_graph["relay_id"][i]["id"]
            self.global_fingerprint.add(fingerprint)
            self.__logger.debug("%s [relay: %s ]", title, fingerprint)
            self.render_graph_new(
                i,
                fingerprint,
                self.data_for_graph,
                ylabel,
                title,
                graph_type=0,
                color="maroon",
            )

    def graph_for_tor_partial_block(self) -> None:
        """
        Basic graph for the percentage of websites partially blocking tor for the given Tor exit relay.
        """
        title = "Checks the percentage of websites partially blocking tor nodes"
        ylabel = "Percentage where Tor partially-blocked percentage\n (dom_analyze) (%)"
        length = len(self.data_for_graph["relay_id"])
        for i in range(0, length):
            fingerprint = self.data_for_graph["relay_id"][i]["id"]
            self.global_fingerprint.add(fingerprint)
            self.__logger.debug("%s [relay: %s ]", title, fingerprint)
            self.render_graph_new(
                i,
                fingerprint,
                self.data_for_graph,
                ylabel,
                title,
                graph_type=1,
                color="orange",
            )

    def graph_for_both_block(self) -> None:
        """
        Contains the basic graph for the percentage of websites blocking both Tor and Control Nodes
        """
        title = "Checks the percentage of websites:\n blocking both the control nodes and tor nodes"
        ylabel = "Percentage of websites: \n Both control nodes & tor are blocked\n (status_check) (%)"
        length = len(self.data_for_graph["relay_id"])
        for i in range(0, length):
            fingerprint = self.data_for_graph["relay_id"][i]["id"]
            self.global_fingerprint.add(fingerprint)
            self.__logger.debug("%s [relay: %s ]", title, fingerprint)
            self.render_graph_new(
                i,
                fingerprint,
                self.data_for_graph,
                ylabel,
                title,
                graph_type=2,
                color="yellow",
            )

    def graph_for_tor_none_block(self) -> None:
        """
        Contains the basic graph for the percentage of websites that let's Tor exit relay access them.
        """
        title = "Checks the percentage of websites unblocked by Tor"
        ylabel = "Percentage:\n Websites unblocked by Tor (%)"
        length = len(self.data_for_graph["relay_id"])
        for i in range(0, length):
            fingerprint = self.data_for_graph["relay_id"][i]["id"]
            self.global_fingerprint.add(fingerprint)
            self.__logger.debug("%s [relay: %s ]", title, fingerprint)
            self.render_graph_new(
                i,
                fingerprint,
                self.data_for_graph,
                ylabel,
                title,
                graph_type=3,
                color="green",
            )

    def export_graph(self, filename: str = "reanalyze.html") -> None:
        """
        Exports the graphs to the html file

        :param filename: Name of the HTML file to export, defaults to "reanalyze.html"
        :type filename: str
        """
        # create an empty webpage with relay.html
        template = self.__jinja_environment.get_template(filename)

        for _, i in enumerate(list(self.global_fingerprint)):
            html_data = template.render(
                fingerprint=i, data=self.graph_name[i], string=self.graph_string
            )
            self.__write_to_file(filename=f"{i}.html", html_data=html_data)

    def render_dashboard(self, filename: str = "dashboard.html") -> None:
        """
        Render the index page, which visitors first see

        :param filename: Name of the HTML file to export, defaults to "index.html"
        :type filename: str
        """
        self.__logger.debug("Rendering %s", filename)

        template = self.__jinja_environment.get_template("dashboard.html")
        html_data = template.render(data=self.data_for_graph)

        self.__write_to_file(filename=filename, html_data=html_data)
