import os.path
import sqlite3
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class SQLite:
    def __init__(self, params):
        self.params = params
        self.check_if_db_exists()

    # Submits given results to the SQLite database
    def submit(self):

        # Set database connection
        conn = sqlite3.connect(self.params['db_file'])

        # Prepare the SQL query
        sql_query = "INSERT INTO captcha (measurement, url, captcha_sign, headless_mode, html_data, result) VALUES (?, ?, ?, ?, ?, ?)"
        sql_params = (self.params['method'],
                      self.params['url'],
                      self.params['captcha_sign'],
                      self.params['headless_mode'],
                      self.params['html_data'],
                      self.params['result'])

        logger.debug(sql_query)
        logger.debug(sql_params)

        # Try to connect to the database
        try:
            conn.cursor().execute(sql_query, sql_params)
            conn.commit()

        except Exception as err:
            logger.critical(
                'Double check the SQL query because sqlite3.connect.cursor.execute() says: %s' % err)

        conn.close()

    # Creat the database tables if the SQLite file doesn't exist

    def check_if_db_exists(self):
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
                                	measurement TEXT,
                                	url TEXT,
                                	captcha_sign TEXT,
                                	headless_mode TEXT,
                                    html_data TEXT,
                                	result TEXT,
                                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                                    )'''

        conn.cursor().execute(sql_query_create_table)
        conn.commit()
        conn.close()
