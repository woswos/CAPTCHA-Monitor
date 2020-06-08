import pytest
import os
from captchamonitor.utils.queue import Queue
import sqlite3
import random
import string


def randomString(stringLength=10):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))


os.environ['CM_DB_FILE_PATH'] = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'cm.db')
db_file = os.environ['CM_DB_FILE_PATH']

job_1 = {'method': randomString(),
         'url': randomString(),
         'captcha_sign': randomString(),
         'additional_headers': randomString(),
         'exit_node': randomString(),
         'tbb_security_level': randomString()}

job_2 = {'method': randomString(),
         'url': randomString(),
         'captcha_sign': randomString(),
         'additional_headers': randomString(),
         'exit_node': randomString(),
         'tbb_security_level': randomString()}


@pytest.fixture
def fresh_queue():
    # Remove the existing test db
    if os.path.exists(db_file):
        os.remove(db_file)

    # Create a new test queue
    queue = Queue()
    return queue


def test_queue_creation(fresh_queue):
    assert fresh_queue.get_job() == None


def test_queue_add_job(fresh_queue):
    fresh_queue.add_job(job_1)
    job = fresh_queue.get_job()
    assert job['url'] == job_1['url']


def test_queue_remove_job_with_single_job(fresh_queue):
    fresh_queue.add_job(job_1)

    # Remove the job internally
    job = fresh_queue.get_job()

    assert fresh_queue.get_job() == None


def test_queue_remove_job_with_multiple_job(fresh_queue):
    fresh_queue.add_job(job_1)
    fresh_queue.add_job(job_2)

    # Remove the first job internally
    job = fresh_queue.get_job()

    # Get the remaining jobs, which should be job 2
    job = fresh_queue.get_job()

    assert job['url'] == job_2['url']
