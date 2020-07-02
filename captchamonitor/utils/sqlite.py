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
                'is_data_modified': 'TEXT',
                'html_data': 'TEXT',
                'requests': 'TEXT',
                'exit_node': 'TEXT',
                'tbb_security_level': 'TEXT',
                'browser_version': 'TEXT',
                'expected_hash': 'TEXT',
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
                'expected_hash': 'TEXT',
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
                'expected_hash': 'TEXT',
            },
            'relays':
            {
                'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
                'last_updated': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
                'fingerprint': 'TEXT UNIQUE',
                'address': 'TEXT UNIQUE',
                'is_ipv4_exiting_allowed': 'TEXT',
                'is_ipv6_exiting_allowed': 'TEXT',
                'country': 'TEXT',
                'status': 'TEXT',
                'performed_tests': 'TEXT',
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
        self.relays_table_name = 'relays'

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

    def insert_entry_into_table(self, table, data, ignore_existing=False):
        """
        Inserts a given entry into a given table
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

        sql_query = 'INTO %s (%s) VALUES (%s)' % (table_name,
                                                  data_fields[:-1],
                                                  data_q_marks[:-1]
                                                  )

        if ignore_existing:
            sql_query = 'INSERT OR IGNORE ' + sql_query
        else:
            sql_query = 'INSERT ' + sql_query

        self.logger.debug(sql_query)
        self.logger.debug(data_values)

        cur = conn.cursor()

        # Try to connect to the database
        try:
            cur.execute(sql_query, data_values)
            conn.commit()

        except Exception as err:
            self.logger.critical('sqlite3.execute() at insert_entry_into_table() says: %s' % err)

        conn.close()

    def get_table_entries(self, table, columns=['*'], identifiers=''):
        """
        Gets the given entries in a given table
        Gets all values if no columns are provided
        Uses the indentifiers for WHERE clause
        """

        table_name = table
        db_file = self.db_file

        # Set database connection
        conn = sqlite3.connect(db_file)

        sql_base = 'SELECT'

        for column in columns:
            sql_base += ' %s,' % column

        sql_table = ' FROM %s' % table_name

        sql_where = ' WHERE'
        for field in identifiers:
            sql_where += ' %s="%s" AND' % (field, identifiers[field])

        if identifiers != '':
            sql_query = sql_base[:-1] + sql_table + sql_where[:-4]
        else:
            sql_query = sql_base[:-1] + sql_table

        self.logger.debug(sql_query)

        cur = conn.cursor()

        # Try to connect to the database
        try:
            cur.execute(sql_query)
            conn.commit()

        except Exception as err:
            self.logger.critical('sqlite3.execute() at get_table_entries() says: %s' % err)

        result = cur.fetchall()

        conn.close()

        final = []
        # Try to place returned data into a dictionary otherwise no data was returned
        try:
            for i in range(len(result)):
                final.append(dict(zip([c[0] for c in cur.description], result[i])))
        except:
            final = None

        return final

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

    def update_table_entry(self, table, data, identifiers):
        """
        Updates a specific table entry with given data using given identifiers
        """

        table_name = table
        db_file = self.db_file

        # Set database connection
        conn = sqlite3.connect(db_file)

        sql_table = 'UPDATE %s ' % table_name

        sql_set = 'SET '
        sql_set_values = []
        for field in data:
            sql_set += ' %s=?,' % field
            sql_set_values.append(data[field])

        sql_where = ' WHERE'
        sql_where_values = []
        for field in identifiers:
            sql_where += ' %s=? AND' % field
            sql_where_values.append(identifiers[field])

        sql_query = sql_table + sql_set[:-1] + sql_where[:-4]
        data_values = sql_set_values + sql_where_values

        self.logger.debug(sql_query)
        self.logger.debug(data_values)

        cur = conn.cursor()

        # Try to connect to the database
        try:
            cur.execute(sql_query, data_values)
            conn.commit()

        except Exception as err:
            self.logger.critical(
                'sqlite3.execute() at update_table_entry() says: %s' % err)

        conn.close()

    def remove_table_entry(self, table, identifiers):
        """
        Removes a specific table entry with given identifiers
        """

        table_name = table
        db_file = self.db_file

        # Set database connection
        conn = sqlite3.connect(db_file)

        sql_table = 'DELETE from %s ' % table_name

        sql_where = ' WHERE'
        sql_where_values = []
        for field in identifiers:
            sql_where += ' %s=? AND' % field
            sql_where_values.append(identifiers[field])

        sql_query = sql_table + sql_where[:-4]
        data_values = sql_where_values

        self.logger.debug(sql_query)
        self.logger.debug(data_values)

        cur = conn.cursor()

        # Try to connect to the database
        try:
            cur.execute(sql_query, data_values)
            conn.commit()

        except Exception as err:
            self.logger.critical(
                'sqlite3.execute() at remove_table_entry() says: %s' % err)

        conn.close()

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
