import os
import sqlite3
import logging


class SQLite:
    def __init__(self):
        """
        The class that communicates with the database directly
        """
        tables = {
            'results':
            {
                'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
                'timestamp': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
                'method': 'TEXT',
                'url': 'TEXT',
                'captcha_sign': 'TEXT',
                'is_captcha_found': 'TEXT',
                'html_data': 'TEXT',
                'requests': 'TEXT',
                'exit_node': 'TEXT',
                'tbb_security_level': 'TEXT',
                'browser_version': 'TEXT',
            },
            'queue':
            {
                'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
                'claimed_by': 'TEXT DEFAULT "None"',
                'method': 'TEXT',
                'url': 'TEXT',
                'captcha_sign': 'TEXT',
                'additional_headers': 'TEXT',
                'exit_node': 'TEXT',
                'tbb_security_level': 'TEXT',
                'browser_version': 'TEXT',
            },
            'failed':
            {
                'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
                'method': 'TEXT',
                'url': 'TEXT',
                'captcha_sign': 'TEXT',
                'additional_headers': 'TEXT',
                'exit_node': 'TEXT',
                'tbb_security_level': 'TEXT',
                'browser_version': 'TEXT',
            }
        }

        self.logger = logging.getLogger(__name__)

        try:
            self.db_file = os.environ['CM_DB_FILE_PATH']
        except Exception as err:
            self.logger.error('CM_DB_FILE_PATH environment variable is not set: %s', err)

        self.tables = tables
        self.queue_table_name = 'queue'
        self.results_table_name = 'results'
        self.failed_table_name = 'failed'

    def check_if_db_exists(self):
        """
        Creates the database and its tables if the SQLite file doesn't exist
        """
        db_file = self.db_file
        tables = self.tables

        # Return if the database already exists
        if os.path.isfile(db_file) and os.access(db_file, os.R_OK):
            self.logger.debug('The SQLite database already exists, skipping the creation')
            return

        self.logger.info('The SQLite database does not exist, creating it now')

        open(db_file, 'w').close()

        # Set database connection
        conn = sqlite3.connect(db_file)

        # Create listed tables
        for table in tables:
            # SQL query to create the tables for the first time run
            create_table = 'CREATE TABLE %s (' % table

            # Insert field values
            for field in tables[table]:
                create_table += ' %s %s,' % (field, tables[table][field])

            # Replace the last comma with ')' to complete the query
            create_table = create_table[:-1] + ')'

            conn.cursor().execute(create_table)

        conn.commit()
        conn.close()

    def insert_job_into_table(self, table, data):
        """
        Inserts given job into the given table
        """

        table_name = table
        db_file = self.db_file

        # Set database connection
        conn = sqlite3.connect(db_file)

        data_fields = ''
        data_q_marks = ''
        data_values = []
        for field in data:
            data_fields += '%s,' % field
            data_q_marks += '?,'
            data_values.append(data[field])

        sql_query = 'INSERT INTO %s (%s) VALUES (%s)' % (table_name,
                                                         data_fields[:-1],
                                                         data_q_marks[:-1]
                                                         )

        self.logger.debug(sql_query)
        self.logger.debug(data_values)

        cur = conn.cursor()

        # Try to connect to the database
        try:
            cur.execute(sql_query, data_values)
            conn.commit()

        except Exception as err:
            self.logger.critical('sqlite3.execute() at insert_job() says: %s' % err)

        conn.close()

    def count_table_entries(self, table):
        """
        Counts the number of entries in a given table
        """

        table_name = table
        db_file = self.db_file

        # Set database connection
        conn = sqlite3.connect(db_file)

        # Prepare the SQL query
        sql_query = 'SELECT count(id) FROM %s' % table_name

        self.logger.debug(sql_query)

        cur = conn.cursor()

        # Try to connect to the database
        try:
            cur.execute(sql_query)
            conn.commit()

        except Exception as err:
            self.logger.critical('sqlite3.execute() at count_table_entries() says: %s' % err)

        result = cur.fetchone()[0]

        conn.close()

        return result

    def claim_first_uncompleted_job(self, worker_id):
        """
        Claims the first uncompleted job in the queue
        """

        table_name = self.queue_table_name
        db_file = self.db_file

        # Set database connection
        conn = sqlite3.connect(db_file)

        sql_query = '''UPDATE %s SET claimed_by = "%s"
                    WHERE id = (SELECT min(id) FROM %s WHERE claimed_by = "None")''' % (
                    table_name, worker_id, table_name)

        self.logger.debug(sql_query)

        cur = conn.cursor()

        # Try to connect to the database
        try:
            cur.execute(sql_query)
            conn.commit()

        except Exception as err:
            self.logger.critical(
                'sqlite3.execute() at claim_first_uncompleted_job() says: %s' % err)

        conn.close()

    def get_claimed_job(self, worker_id):
        """
        Gets the details of the claimed job
        Returns none if no job was claimed or there are no jobs in the queue
        """

        table_name = self.queue_table_name
        db_file = self.db_file

        # Set database connection
        conn = sqlite3.connect(db_file)

        # Prepare the SQL query
        sql_query = 'SELECT * FROM %s WHERE claimed_by = "%s"' % (table_name, worker_id)

        self.logger.debug(sql_query)

        cur = conn.cursor()

        # Try to connect to the database
        try:
            cur.execute(sql_query)
            conn.commit()

        except Exception as err:
            self.logger.critical('sqlite3.execute() at get_claimed_job() says: %s' % err)

        result = cur.fetchall()

        conn.close()

        # Try to place returned data into a dictionary otherwise no data was returned
        try:
            result = dict(zip([c[0] for c in cur.description], result[0]))
        except:
            result = None

        return result

    def get_job_with_id(self, job_id):
        """
        Gets the details of the job with a given id
        Returns none if no job was claimed or there are no jobs in the queue
        """

        table_name = self.queue_table_name
        db_file = self.db_file

        # Set database connection
        conn = sqlite3.connect(db_file)

        # Prepare the SQL query
        sql_query = 'SELECT * FROM %s WHERE id = "%s"' % (table_name, job_id)

        self.logger.debug(sql_query)

        cur = conn.cursor()

        # Try to connect to the database
        try:
            cur.execute(sql_query)
            conn.commit()

        except Exception as err:
            self.logger.critical('sqlite3.execute() at get_job_with_id() says: %s' % err)

        result = cur.fetchall()

        conn.close()

        # Try to place returned data into a dictionary otherwise no data was returned
        try:
            result = dict(zip([c[0] for c in cur.description], result[0]))
        except:
            result = None

        return result

    def remove_job(self, job_id):
        """
        Removes the job with given id
        """

        table_name = self.queue_table_name
        db_file = self.db_file

        # Set database connection
        conn = sqlite3.connect(db_file)

        # Prepare the SQL query
        sql_query = 'DELETE from %s WHERE id = "%s"' % (table_name, job_id)

        self.logger.debug(sql_query)

        cur = conn.cursor()

        # Try to connect to the database
        try:
            cur.execute(sql_query)
            conn.commit()

        except Exception as err:
            self.logger.critical('sqlite3.execute() at remove_job() says: %s' % err)

        conn.close()
