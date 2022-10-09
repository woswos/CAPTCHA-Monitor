import os
import time
import shutil
import fnmatch
import logging
import tarfile
import tempfile
from datetime import datetime

import requests

from captchamonitor.utils.exceptions import (
    CollectorDownloadError,
    CollectorConnectionError,
)


class Collector:
    """
    Gets the absolute path to the consensus file from cache or downloads it from
    Collector if it doesn't exist
    """

    def __init__(self) -> None:
        """
        Initialize Collector
        """
        # Private class attributes
        self.__logger = logging.getLogger(__name__)
        self.__url_consensuses_recent: str = (
            "https://collector.torproject.org/recent/relay-descriptors/consensuses/"
        )
        self.__url_consensuses_archive: str = (
            "https://collector.torproject.org/archive/relay-descriptors/consensuses/"
        )
        self.__consensus_dir: str = "/tmp/cm-consensus"
        self.__num_retries_on_fail: int = 3
        self.__delay_in_seconds_between_retries: int = 3

        # Remove if a file with same name was created earlier
        if os.path.isfile(self.__consensus_dir):
            os.remove(self.__consensus_dir)

        # Create the consensus directory if doesn't exist'
        if not os.path.isdir(self.__consensus_dir):
            os.makedirs(self.__consensus_dir)

    @staticmethod
    def __get_date_str(consensus_date: datetime) -> str:
        """
        Convert date to correct format, round down to the last hour

        :param consensus_date: The date for valid-after timestamp of the consensus document
        :type consensus_date: datetime
        :return: String representation of the given timestamp
        :rtype: str
        """
        return consensus_date.strftime("%Y-%m-%d-%H-00-00")

    def __download_consensus_from_recent(self, consensus_date: datetime) -> None:
        """
        Downloads from the Collector's recent page

        :param consensus_date: The date for valid-after timestamp of the consensus document
        :type consensus_date: datetime
        :raises CollectorDownloadError: If cannot connect to Collector
        """
        date_str = self.__get_date_str(consensus_date)

        self.__logger.debug("Using the list from recent consensuses")

        file_name = f"{date_str}-consensus"
        url = f"{self.__url_consensuses_recent}{file_name}"
        file_path = os.path.join(self.__consensus_dir, file_name)

        try:
            # Download the consensus file directly to the consensus directory
            with open(file_path, "wb") as file:
                file.write(requests.get(url).content)

        except Exception as exception:
            self.__logger.debug(
                "Cannot download requested consensus file: %s",
                exception,
            )
            raise CollectorDownloadError from exception

    def __download_consensus_from_archive(self, consensus_date: datetime) -> None:
        """
        Downloads from the Collector's archive page

        :param consensus_date: The date for valid-after timestamp of the consensus document
        :type consensus_date: datetime
        :raises CollectorDownloadError: If cannot connect to Collector
        """
        self.__logger.debug("Using the list from consensuses archive")

        # Create a temporary directory and download the consensus archive
        with tempfile.TemporaryDirectory() as download_dir:
            folder_name = "consensuses-%s-%s" % (
                consensus_date.strftime("%Y"),
                consensus_date.strftime("%m"),
            )
            archive_name = folder_name + ".tar.xz"
            archive_path = os.path.join(download_dir, archive_name)
            extracted_path = os.path.join(download_dir, folder_name)
            url = f"{self.__url_consensuses_archive}{archive_name}"

            try:
                # Download the consensus archive to a temporary location
                with open(archive_path, "wb") as file:
                    file.write(requests.get(url).content)

            except Exception as exception:
                self.__logger.debug(
                    "Cannot download requested consensus file: %s",
                    exception,
                )
                raise CollectorDownloadError from exception

            # Extract the archive
            with tarfile.open(archive_path) as archive:
                def is_within_directory(directory, target):
                    
                    abs_directory = os.path.abspath(directory)
                    abs_target = os.path.abspath(target)
                
                    prefix = os.path.commonprefix([abs_directory, abs_target])
                    
                    return prefix == abs_directory
                
                def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
                
                    for member in tar.getmembers():
                        member_path = os.path.join(path, member.name)
                        if not is_within_directory(path, member_path):
                            raise Exception("Attempted Path Traversal in Tar File")
                
                    tar.extractall(path, members, numeric_owner=numeric_owner) 
                    
                
                safe_extract(archive, download_dir)

            # Recursively move files
            for day_folder in os.listdir(extracted_path):
                for consensus_file in os.listdir(
                    os.path.join(extracted_path, day_folder)
                ):
                    try:
                        shutil.move(
                            os.path.join(extracted_path, day_folder, consensus_file),
                            self.__consensus_dir,
                        )

                    except shutil.Error as exception:
                        # We can simply skip already existing files
                        self.__logger.debug(
                            "This consensus file already exists: %s",
                            exception,
                        )

    def get_consensus(self, consensus_date: datetime) -> str:
        """
        Gets the absolute path to the consensus file from cache or downloads it if it doesn't exist

        :param consensus_date: The date for valid-after timestamp of the consensus document
        :type consensus_date: datetime
        :raises CollectorDownloadError: If requested configuration wasn't found locally and downloaded from Collector
        :return: Absolute path to the consensus file
        :rtype: str
        """
        date_str = self.__get_date_str(consensus_date)

        # Try multiple times
        for _ in range(self.__num_retries_on_fail):
            # Find the requested consensus from the cache
            for file in os.listdir(self.__consensus_dir):
                if fnmatch.fnmatch(file, "*" + date_str + "*"):
                    return os.path.join(self.__consensus_dir, file)

            # If we are here, it means that the requested consensus is not cached yet
            self.__logger.debug(
                "Requested consensus file is not cached yet, downloading from Collector"
            )
            self.download_consensus(consensus_date)
            time.sleep(self.__delay_in_seconds_between_retries)

        self.__logger.warning(
            "Could not source the requested consensus file after many tries"
        )
        raise CollectorDownloadError

    def download_consensus(self, consensus_date: datetime) -> None:
        """
        Downloads the consensus document for the specified date from CollecTor

        :param consensus_date: The date for valid-after timestamp of the consensus document
        :type consensus_date: datetime
        :raises CollectorConnectionError: If cannot connect to Collector
        """
        date_str = self.__get_date_str(consensus_date)

        try:
            # Check for recent consensuses first
            recent_consensuses = requests.get(self.__url_consensuses_recent).text

        except Exception as exception:
            self.__logger.debug(
                "Cannot connect to Collector: %s",
                exception,
            )
            raise CollectorConnectionError from exception

        if date_str in recent_consensuses:
            self.__download_consensus_from_recent(consensus_date)
        else:
            self.__download_consensus_from_archive(consensus_date)

    def remove_consensus_file(self, consensus_date: datetime) -> None:
        """
        Finds the consensus document that was published at given date and deletes it

        :param consensus_date: the date for valid-after timestamp of the consensus document
        :type consensus_date: datetime
        """
        date_str = self.__get_date_str(consensus_date)

        if os.path.exists(self.__consensus_dir):
            file = os.path.join(self.__consensus_dir, f"{date_str}-consensus")
            try:
                os.remove(file)

            except FileNotFoundError:
                pass

            self.__logger.debug("Removed the consensus file %s", file)
