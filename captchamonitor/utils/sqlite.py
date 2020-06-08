import os.path
import sqlite3
import logging

logger = logging.getLogger(__name__)


class SQLite:
    def __init__(self, db_file):
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
                'all_headers': 'TEXT',
                'request_headers': 'TEXT',
                'response_headers': 'TEXT',
                'exit_node': 'TEXT',
                'tbb_security_level': 'TEXT',
            },
            'queue':
            {
                'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
                'method': 'TEXT',
                'url': 'TEXT',
                'captcha_sign': 'TEXT',
                'additional_headers': 'TEXT',
                'exit_node': 'TEXT',
                'tbb_security_level': 'TEXT',
            }
        }

        self.db_file = db_file
        self.tables = tables
        self.queue_table_name = 'queue'
        self.results_table_name = 'results'

    def check_if_db_exists(self):
        """
        Creates the database and its tables if the SQLite file doesn't exist
        """
        db_file = self.db_file
        tables = self.tables

        # Return if the database already exists
        if os.path.isfile(db_file) and os.access(db_file, os.R_OK):
            logger.debug('The SQLite database already exists, skipping the creation')
            return

        logger.info('The SQLite database does not exist, creating it now')

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

    def insert_job(self, data):
        """
        Inserts a new job into the database
        """

        table_name = self.queue_table_name
        db_file = self.db_file

        # Set database connection
        conn = sqlite3.connect(db_file)

        data_fields = ''
        data_values = ''
        for field in data:
            data_fields += '%s,' % field
            data_values += '"%s",' % data[field]

        sql_query = 'INSERT INTO %s (%s) VALUES (%s)' % (table_name,
                                                         data_fields[:-1],
                                                         data_values[:-1]
                                                         )

        logger.debug(sql_query)

        cur = conn.cursor()

        # Try to connect to the database
        try:
            cur.execute(sql_query)
            conn.commit()

        except Exception as err:
            logger.critical('sqlite3.connect.cursor.execute() at insert_job() says: %s' % err)

        conn.close()

    def get_first_uncompleted_job(self):
        """
        Gets the details of the first uncompleted job in the queue
        Returns none if there are no jobs in the queue
        """

        table_name = self.queue_table_name
        db_file = self.db_file

        # Set database connection
        conn = sqlite3.connect(db_file)

        # Prepare the SQL query
        sql_query = 'SELECT * FROM %s ORDER BY id ASC LIMIT 1' % table_name

        logger.debug(sql_query)

        cur = conn.cursor()

        # Try to connect to the database
        try:
            cur.execute(sql_query)
            conn.commit()

        except Exception as err:
            logger.critical('sqlite3.connect.cursor.execute() says: %s' % err)

        result = cur.fetchall()

        conn.close()

        # Try to place returned data into a dictionary otherwise no data was returned
        try:
            result = dict(zip([c[0] for c in cur.description], result[0]))
        except:
            result = None

        return result

    def remove_job(self, id):
        """
        Removes the job with given id
        """

        table_name = self.queue_table_name
        db_file = self.db_file

        # Set database connection
        conn = sqlite3.connect(db_file)

        # Prepare the SQL query
        sql_query = 'DELETE from %s WHERE id = "%s"' % (table_name, id)

        logger.debug(sql_query)

        cur = conn.cursor()

        # Try to connect to the database
        try:
            cur.execute(sql_query)
            conn.commit()

        except Exception as err:
            logger.critical('sqlite3.connect.cursor.execute() says: %s' % err)

        conn.close()

    def insert_result(self, data):
        """
        Inserts the result of a job into the database
        """

        table_name = self.results_table_name
        db_file = self.db_file

        # Set database connection
        conn = sqlite3.connect(db_file)

        data_fields = ''
        data_values = ''
        for field in data:
            data_fields += '%s,' % field
            data_values += '"%s",' % data[field]

        sql_query = 'INSERT INTO %s (%s) VALUES (%s)' % (table_name,
                                                         data_fields[:-1],
                                                         data_values[:-1]
                                                         )

        logger.debug(sql_query)
        print(sql_query)
        cur = conn.cursor()

        # Try to connect to the database
        try:
            cur.execute(sql_query)
            conn.commit()

        except Exception as err:
            logger.critical('sqlite3.connect.cursor.execute() at insert_job() says: %s' % err)

        conn.close()
