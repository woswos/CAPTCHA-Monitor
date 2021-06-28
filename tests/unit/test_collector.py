import os
import shutil
from datetime import datetime, timedelta

from captchamonitor.utils.collector import Collector


class TestCollector:
    @classmethod
    def setup_class(cls):
        cls.recent_datetime = datetime.now() - timedelta(hours=1)
        cls.archive_datetime = datetime.now() - timedelta(hours=100)
        cls.consensus_dir = Collector()._Collector__consensus_dir
        cls.recent_consensus_str = (
            cls.recent_datetime.strftime("%Y-%m-%d-%H-00-00") + "-consensus"
        )
        cls.archive_consensus_str = (
            cls.archive_datetime.strftime("%Y-%m-%d-%H-00-00") + "-consensus"
        )
        shutil.rmtree(cls.consensus_dir)

        cls.collector = Collector()

        # Make sure the directory is empty
        assert len(os.listdir(cls.consensus_dir)) == 0

    def test_download_consensus_recent(self):
        # Download the consensus file
        self.collector.download_consensus(self.recent_datetime)

        # Check if file was downloaded
        assert self.recent_consensus_str in os.listdir(self.consensus_dir)

    def test_download_consensus_archive(self):
        # Download the consensus file
        self.collector.download_consensus(self.archive_datetime)

        # Check if file was downloaded
        assert self.archive_consensus_str in os.listdir(self.consensus_dir)

    def test_remove_consensus_file(self):
        # Download the consensus file
        self.collector.download_consensus(self.recent_datetime)

        # Check if file was downloaded
        assert self.recent_consensus_str in os.listdir(self.consensus_dir)

        # Delete the consensus file
        self.collector.remove_consensus_file(self.recent_datetime)

        # Make sure the directory is empty
        assert self.recent_consensus_str not in os.listdir(self.consensus_dir)

    def test_get_consensus_recent(self):
        # Download the consensus file
        file = self.collector.get_consensus(self.recent_datetime)

        assert file.split("/")[-1] == self.recent_consensus_str
