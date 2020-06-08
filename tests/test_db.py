import pytest
import os
from captchamonitor.utils.sqlite import SQLite
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

result_1 = {'method': randomString(),
            'url': randomString(),
            'captcha_sign': randomString(),
            'is_captcha_found': 0,
            'html_data': randomString(),
            'all_headers': randomString(),
            'request_headers': randomString(),
            'response_headers': randomString(),
            'exit_node': None,
            'tbb_security_level': None}


@pytest.fixture
def fresh_db():
    # Remove the existing test db
    if os.path.exists(db_file):
        os.remove(db_file)

    # Create a new test db
    db = SQLite()
    db.check_if_db_exists()
    return db


def test_db_creation(fresh_db):
    assert os.path.exists(db_file) == True


def test_db_insert_job(fresh_db):
    fresh_db.insert_job(job_1)

    # Check if the value was inserted
    sql_query = 'SELECT * FROM queue'
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute(sql_query)
    result = cur.fetchall()
    result = dict(zip([c[0] for c in cur.description], result[0]))
    conn.commit()

    assert result['url'] == job_1['url']


def test_db_get_uncompleted_job_with_no_job(fresh_db):
    job = fresh_db.get_first_uncompleted_job()
    assert job == None


def test_db_get_uncompleted_job_with_job(fresh_db):
    fresh_db.insert_job(job_1)

    job = fresh_db.get_first_uncompleted_job()

    assert job['url'] == job_1['url']


def test_db_get_uncompleted_job_with_multiple_jobs(fresh_db):
    fresh_db.insert_job(job_1)
    fresh_db.insert_job(job_2)

    # Should give priority to first inserted job
    job = fresh_db.get_first_uncompleted_job()

    assert job['url'] == job_1['url']


def test_db_remove_job(fresh_db):
    fresh_db.insert_job(job_1)

    # Get the job
    job = fresh_db.get_first_uncompleted_job()

    # Delete the job
    fresh_db.remove_job(job['id'])

    # Check if the job was deleted
    sql_query = 'SELECT * FROM queue'
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute(sql_query)
    result = cur.fetchone()
    conn.commit()

    assert result == None


def test_db_remove_job_with_multiple_jobs_in_the_queue(fresh_db):
    fresh_db.insert_job(job_1)
    fresh_db.insert_job(job_2)

    # Get the job
    job = fresh_db.get_first_uncompleted_job()

    # Delete the first job
    fresh_db.remove_job(job['id'])

    # Check if the job was deleted
    sql_query = 'SELECT * FROM queue'
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute(sql_query)
    result = cur.fetchall()
    result = dict(zip([c[0] for c in cur.description], result[0]))
    conn.commit()

    assert result['url'] == job_2['url']


def test_db_insert_result(fresh_db):
    fresh_db.insert_result(result_1)

    # Check if the value was inserted
    sql_query = 'SELECT * FROM results'
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute(sql_query)
    result = cur.fetchall()
    result = dict(zip([c[0] for c in cur.description], result[0]))
    conn.commit()

    assert result['url'] == result_1['url']
