import pytest
import os
from captchamonitor.utils.sqlite import SQLite
import sqlite3
import random
import string


def randomString(size=10, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


os.environ['CM_DB_FILE_PATH'] = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'cm.db')
db_file = os.environ['CM_DB_FILE_PATH']

job_1 = {'method': randomString(),
         'url': randomString(),
         'captcha_sign': randomString(),
         'additional_headers': randomString(),
         'exit_node': randomString(),
         'tbb_security_level': randomString(),
         'browser_version': randomString()}

job_2 = {'method': randomString(),
         'url': randomString(),
         'captcha_sign': randomString(),
         'additional_headers': randomString(),
         'exit_node': randomString(),
         'tbb_security_level': randomString(),
         'browser_version': randomString()}

result_1 = {'method': randomString(),
            'url': randomString(),
            'captcha_sign': randomString(),
            'is_captcha_found': 0,
            'html_data': randomString(),
            'requests': randomString(),
            'exit_node': None,
            'tbb_security_level': None,
            'browser_version': None}


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
    fresh_db.insert_job_into_table(fresh_db.queue_table_name, job_1)

    # Check if the value was inserted
    sql_query = 'SELECT * FROM %s' % fresh_db.queue_table_name
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute(sql_query)
    result = cur.fetchall()
    result = dict(zip([c[0] for c in cur.description], result[0]))
    conn.commit()

    assert result['url'] == job_1['url']


def test_db_get_uncompleted_job_with_no_job(fresh_db):
    worker_id = randomString(32)
    fresh_db.claim_first_uncompleted_job(worker_id)
    job = fresh_db.get_claimed_job(worker_id)
    assert job == None


def test_db_get_uncompleted_job_with_job(fresh_db):
    fresh_db.insert_job_into_table(fresh_db.queue_table_name, job_1)

    worker_id = randomString(32)
    fresh_db.claim_first_uncompleted_job(worker_id)
    job = fresh_db.get_claimed_job(worker_id)

    assert job['url'] == job_1['url']


def test_db_get_uncompleted_job_with_multiple_jobs(fresh_db):
    fresh_db.insert_job_into_table(fresh_db.queue_table_name, job_1)
    fresh_db.insert_job_into_table(fresh_db.queue_table_name, job_2)

    # Should give priority to first inserted job
    worker_id = randomString(32)
    fresh_db.claim_first_uncompleted_job(worker_id)
    job = fresh_db.get_claimed_job(worker_id)

    assert job['url'] == job_1['url']


def test_db_remove_job(fresh_db):
    fresh_db.insert_job_into_table(fresh_db.queue_table_name, job_1)

    # Get the job
    worker_id = randomString(32)
    fresh_db.claim_first_uncompleted_job(worker_id)
    job = fresh_db.get_claimed_job(worker_id)

    # Delete the job
    fresh_db.remove_job(job['id'])

    # Check if the job was deleted
    sql_query = 'SELECT * FROM %s' % fresh_db.queue_table_name
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute(sql_query)
    result = cur.fetchone()
    conn.commit()

    assert result == None


def test_db_remove_job_with_multiple_jobs_in_the_queue(fresh_db):
    fresh_db.insert_job_into_table(fresh_db.queue_table_name, job_1)
    fresh_db.insert_job_into_table(fresh_db.queue_table_name, job_2)

    # Get the job
    worker_id = randomString(32)
    fresh_db.claim_first_uncompleted_job(worker_id)
    job = fresh_db.get_claimed_job(worker_id)

    # Delete the first job
    fresh_db.remove_job(job['id'])

    # Check if the job was deleted
    sql_query = 'SELECT * FROM %s' % fresh_db.queue_table_name
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute(sql_query)
    result = cur.fetchall()
    result = dict(zip([c[0] for c in cur.description], result[0]))
    conn.commit()

    assert result['url'] == job_2['url']


def test_db_insert_result(fresh_db):
    fresh_db.insert_job_into_table(fresh_db.results_table_name, result_1)

    # Check if the value was inserted
    sql_query = 'SELECT * FROM %s' % fresh_db.results_table_name
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute(sql_query)
    result = cur.fetchall()
    result = dict(zip([c[0] for c in cur.description], result[0]))
    conn.commit()

    assert result['url'] == result_1['url']


def test_db_insert_failed(fresh_db):
    fresh_db.insert_job_into_table(fresh_db.failed_table_name, job_1)

    # Check if the value was inserted
    sql_query = 'SELECT * FROM %s' % fresh_db.failed_table_name
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute(sql_query)
    result = cur.fetchall()
    result = dict(zip([c[0] for c in cur.description], result[0]))
    conn.commit()

    assert result['url'] == job_1['url']
