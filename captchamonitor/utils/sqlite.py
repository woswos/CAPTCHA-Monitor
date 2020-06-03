import os.path
import sqlite3
import logging

logger = logging.getLogger(__name__)


class SQLite:
    def __init__(self, params):
        self.params = params
        self.check_if_db_exists()

    def insert_job(self, data):
        """
        Submits given results to the SQLite database
        """

        # Set database connection
        conn = sqlite3.connect(self.params['db_file'])

        # Prepare the SQL query
        sql_query = '''INSERT INTO captcha (
                    method,
                    url,
                    captcha_sign,
                    request_headers,
                    exit_node,
                    is_completed
                    ) VALUES (?, ?, ?, ?, ?, ?)'''
        sql_params = (data['method'],
                      data['url'],
                      data['captcha_sign'],
                      data['additional_headers'],
                      data['exit_node'],
                      0
                      )

        logger.debug(sql_query)
        logger.debug(sql_params)

        cur = conn.cursor()

        # Try to connect to the database
        try:
            cur.execute(sql_query, sql_params)
            conn.commit()

        except Exception as err:
            logger.critical('sqlite3.connect.cursor.execute() at insert_job() says: %s' % err)

        conn.close()

    def insert_results(self):
        """
        Submits given results to the SQLite database
        """

        # Set database connection
        conn = sqlite3.connect(self.params['db_file'])

        # Prepare the SQL query
        sql_query = '''INSERT INTO captcha (
                    method,
                    url,
                    captcha_sign,
                    html_data,
                    all_headers,
                    request_headers,
                    response_headers,
                    is_captcha_found,
                    exit_node,
                    is_completed
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
        sql_params = (self.params['method'],
                      self.params['url'],
                      self.params['captcha_sign'],
                      self.params['html_data'],
                      self.params['all_headers'],
                      self.params['request_headers'],
                      self.params['response_headers'],
                      self.params['is_captcha_found'],
                      self.params['exit_node'],
                      1
                      )

        logger.debug(sql_query)
        logger.debug(sql_params)

        cur = conn.cursor()

        # Try to connect to the database
        try:
            cur.execute(sql_query, sql_params)
            conn.commit()

        except Exception as err:
            logger.critical('sqlite3.connect.cursor.execute() at insert_results() says: %s' % err)

        conn.close()

    def update_results(self):
        """
        Submits given results to the SQLite database
        """

        # Set database connection
        conn = sqlite3.connect(self.params['db_file'])

        # Prepare the SQL query
        # I know this is a bad practice but I will fix it
        sql_query = '''UPDATE captcha SET
                    html_data = ?,
                    all_headers = ?,
                    request_headers = ?,
                    response_headers = ?,
                    is_captcha_found = ?,
                    exit_node = ?,
                    is_completed = ?
                    WHERE id = ''' + str(self.params['job_id'])
        sql_params = (self.params['html_data'],
                      self.params['all_headers'],
                      self.params['request_headers'],
                      self.params['response_headers'],
                      self.params['is_captcha_found'],
                      self.params['exit_node'],
                      1
                      )

        logger.debug(sql_query)
        logger.debug(sql_params)

        cur = conn.cursor()

        # Try to connect to the database
        try:
            cur.execute(sql_query, sql_params)
            conn.commit()

        except Exception as err:
            logger.critical('sqlite3.connect.cursor.execute() at update_results() says: %s' % err)

        conn.close()

    def get_number_of_not_completed_jobs(self):
        # Set database connection
        conn = sqlite3.connect(self.params['db_file'])

        # Prepare the SQL query
        sql_query = 'SELECT count(*) FROM captcha WHERE is_completed = 0'

        logger.debug(sql_query)

        cur = conn.cursor()

        # Try to connect to the database
        try:
            cur.execute(sql_query)

        except Exception as err:
            logger.critical('sqlite3.connect.cursor.execute() at get_number_of_not_completed_jobs() says: %s' % err)

        result = cur.fetchone()[0]

        conn.close()

        return result

    def get_first_not_completed_job(self):
        # Set database connection
        conn = sqlite3.connect(self.params['db_file'])

        # Prepare the SQL query
        sql_query = 'SELECT * FROM captcha WHERE id = (SELECT min(id) FROM captcha WHERE is_completed = 0)'

        logger.debug(sql_query)

        cur = conn.cursor()

        # Try to connect to the database
        try:
            cur.execute(sql_query)

        except Exception as err:
            logger.critical('sqlite3.connect.cursor.execute() says: %s' % err)

        result = cur.fetchall()

        # Place returned data into a dictionary
        data = dict(zip([c[0] for c in cur.description], result[0]))

        conn.close()

        return data

    def check_if_db_exists(self):
        """
        Creates the database tables if the SQLite file doesn't exist
        """

        output_db = self.params['db_file']

        # Return if the database already exists
        if os.path.isfile(output_db) and os.access(output_db, os.R_OK):
            logger.debug('The SQLite database already exists, skipping the creation')
            return

        logger.info('The SQLite database does not exist, creating it now')

        open(output_db, 'w').close()

        # Set database connection
        conn = sqlite3.connect(output_db)

        # SQL query to create the tables for the first time run
        sql_query_create_table = '''CREATE TABLE captcha (
                                	id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    is_completed INTEGER DEFAULT 0,
                                	method TEXT,
                                	url TEXT,
                                    exit_node TEXT,
                                	captcha_sign TEXT,
                                    html_data TEXT,
                                    all_headers TEXT,
                                    request_headers TEXT,
                                    response_headers TEXT,
                                	is_captcha_found TEXT,
                                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                                    )'''

        conn.cursor().execute(sql_query_create_table)
        conn.commit()
        conn.close()
