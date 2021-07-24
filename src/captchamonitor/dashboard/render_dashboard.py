import os
import shutil
import logging

from jinja2 import Environment, FileSystemLoader
from sqlalchemy.orm import sessionmaker

from captchamonitor.utils.config import Config
from captchamonitor.utils.models import Domain


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

        # Clean the www directory
        self.cleanup_www_folder()

        # Render all pages
        self.render_index()
        self.render_domain_list()

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
