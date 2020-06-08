import pytest
import os
import shutil
from captchamonitor.utils.db_export import export
from captchamonitor.utils.sqlite import SQLite

export_location = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'export')
os.environ['CM_DB_FILE_PATH'] = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'cm.db')
db_file = os.environ['CM_DB_FILE_PATH']


@pytest.fixture
def fresh_db():
    # Remove the existing test db
    if os.path.exists(db_file):
        os.remove(db_file)

    # Remove the existing test export location
    if os.path.exists(export_location):
        shutil.rmtree(export_location)

    # Create a new test db
    db = SQLite()
    db.check_if_db_exists()


def test_db_creation(fresh_db):
    export(export_location)
    assert os.path.exists(export_location) == True
