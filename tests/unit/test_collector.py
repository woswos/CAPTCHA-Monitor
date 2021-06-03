import os
import shutil
import unittest
from datetime import datetime, timedelta

import pytest

from captchamonitor.utils.collector import Collector


class TestCollector(unittest.TestCase):
    def setUp(self):
        self.recent_datetime = datetime.now() - timedelta(hours=1)
        self.archive_datetime = datetime.now() - timedelta(hours=100)
        self.consensus_dir = Collector()._Collector__consensus_dir
        self.recent_consensus_str = (
            self.recent_datetime.strftime("%Y-%m-%d-%H-00-00") + "-consensus"
        )
        self.archive_consensus_str = (
            self.archive_datetime.strftime("%Y-%m-%d-%H-00-00") + "-consensus"
        )
        shutil.rmtree(self.consensus_dir)

        self.collector = Collector()

        # Make sure the directory is empty
        self.assertEqual(len(os.listdir(self.consensus_dir)), 0)

    def test_download_consensus_recent(self):
        # Download the consensus file
        self.collector.download_consensus(self.recent_datetime)

        # Check if file was downloaded
        self.assertIn(self.recent_consensus_str, os.listdir(self.consensus_dir))

    def test_download_consensus_archive(self):
        # Download the consensus file
        self.collector.download_consensus(self.archive_datetime)

        # Check if file was downloaded
        self.assertIn(self.archive_consensus_str, os.listdir(self.consensus_dir))

    def test_remove_consensus_file(self):
        # Download the consensus file
        self.collector.download_consensus(self.recent_datetime)

        # Check if file was downloaded
        self.assertIn(self.recent_consensus_str, os.listdir(self.consensus_dir))

        # Delete the consensus file
        self.collector.remove_consensus_file(self.recent_datetime)

        # Make sure the directory is empty
        self.assertEqual(len(os.listdir(self.consensus_dir)), 0)

    def test_get_consensus_recent(self):
        # Download the consensus file
        file = self.collector.get_consensus(self.recent_datetime)

        self.assertEqual(file.split("/")[-1], self.recent_consensus_str)
