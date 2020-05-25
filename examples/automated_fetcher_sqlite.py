#!/usr/bin/env python2

"""
Check if a web site returns a CloudFlare CAPTCHA using Tor Browser & httplib
and save results into an SQLite database
"""

import time
import sys
import sqlite3
import itertools
import os.path
import logging

sys.path.append("../CAPTCHA-Monitor")
import cloudflared_tor as cf_tor
import cloudflared_httplib as cf_httplib

logger_format = '%(asctime)s :: %(module)s :: %(levelname)s :: %(message)s'
logging.basicConfig(format=logger_format)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# Must use an absolute path (https://stackoverflow.com/a/28126276/10216991)
output_db = '/home/woswos/CAPTCHA-Monitor/examples/results.db'


def main():
    # Creat the database tables if the SQLite file doesn't exist
    check_if_db_exists(output_db)

    url_list = ['http://captcha.wtf',
                'https://captcha.wtf',
                'http://captcha.wtf/complex.html',
                'https://captcha.wtf/complex.html',
                'http://bypass.captcha.wtf',
                'https://bypass.captcha.wtf',
                'http://bypass.captcha.wtf/complex.html',
                'https://bypass.captcha.wtf/complex.html',
                'http://exit11.online',
                'https://exit11.online',
                'http://exit11.online/complex.html',
                'https://exit11.online/complex.html',
                'http://bypass.exit11.online',
                'https://bypass.exit11.online',
                'http://bypass.exit11.online/complex.html',
                'https://bypass.exit11.online/complex.html']

    # The parameters required to run the tests
    params = {}
    results = {}
    params['captcha_sign'] = 'Cloudflare'
    params['tbb_path'] = '/home/woswos/tor-browser_en-US'
    params['headless_mode'] = False # make this True if running on a non-GUI OS

    # Iterate over the url list
    for i, url in enumerate(url_list):
        params['url'] = url

        # Test with httplib
        test_with(cf_httplib, params, output_db)

        # Test with Tor
        test_with(cf_tor, params, output_db)

    logger.info('Completed testing')


# Perform a test with the given paramters and append result to the CSV file
def test_with(method, params, output_db):
    results = method.is_cloudflared(params)
    logger.info('Test result for %s with %s is %s' % (results.get('url'), results.get('method'), results.get('result')))
    submit_to_sqlite_db(output_db, results)


# Submits given results to the SQLite database
def submit_to_sqlite_db(output_db, data):
    # Set database connection
    conn = sqlite3.connect(output_db)

    # Prepare the SQL query
    sql_query = "INSERT INTO captcha (measurement, url, captcha_sign, headless_mode, result) VALUES (?, ?, ?, ?, ?)"
    sql_params = (data['method'], data['url'], data['captcha_sign'], data['headless_mode'], data['result'])

    logger.debug(sql_query)
    logger.debug(sql_params)

    # Try to connect to the database
    try:
        conn.cursor().execute(sql_query, sql_params)
        conn.commit()

    except Exception as err:
        logger.critical('Double check the SQL query because sqlite3.connect.cursor.execute() says: %s' % err)

    conn.close()


# Creat the database tables if the SQLite file doesn't exist
def check_if_db_exists(output_db):

    # Return if the database already exists
    if os.path.isfile(output_db) and os.access(output_db, os.R_OK):
        logger.debug('The SQLite database already exists, skipping the creation')
        return

    logger.info('The SQLite database does not exist, creating it now')

    # Set database connection
    conn = sqlite3.connect(output_db)

    # SQL query to create the tables for the first time run
    sql_query_create_table = '''CREATE TABLE captcha (
                            	id INTEGER PRIMARY KEY AUTOINCREMENT,
                            	measurement TEXT,
                            	url TEXT,
                            	captcha_sign TEXT,
                            	headless_mode TEXT,
                            	result TEXT,
                                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                                )'''

    conn.cursor().execute(sql_query_create_table)
    conn.commit()
    conn.close()


if __name__ == '__main__':
    main()
    sys.exit(0)
