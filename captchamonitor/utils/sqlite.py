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
                # unique ID for this table
                'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
                # the timestamp when the row was inserted
                'timestamp': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
                # name of the desired fetcher to use
                'method': 'TEXT',
                # full URL including the http/https prefix
                'url': 'TEXT',
                # CAPTCHA sign that will be used for CAPTCHA detection
                'captcha_sign': 'TEXT',
                # 1 if CAPTCHA was found, 0 if CAPTCHA was not found
                'is_captcha_found': 'TEXT',
                # 1 if the hash of the received data doesn't match `expected_hash`, otherwise 0
                'is_data_modified': 'TEXT',
                # the HTML data gathered as a result of the fetch
                'html_data': 'TEXT',
                # the HTTP requests in JSON format made by the fether while fetching the URL
                'requests': 'TEXT',
                # IPv4 address of the exit node/relay to use, only required when using Tor
                'exit_node': 'TEXT',
                # only required when using Tor Browser. Possible values: low, medium, or high
                'tbb_security_level': 'TEXT',
                # version of the tool to use, use a single value
                'browser_version': 'TEXT',
                # hash gathered using `captchamonitor md5 -u URL`
                'expected_hash': 'TEXT',
                # version of the captchamonitor
                'captchamonitor_version': 'TEXT',
            },
            'queue':
            {
                # unique ID for this table
                'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
                # workers use this field for assigning jobs to themselves
                'claimed_by': 'TEXT DEFAULT "None"',
                # name of the desired fetcher to use
                'method': 'TEXT',
                # full URL including the http/https prefix
                'url': 'TEXT',
                # CAPTCHA sign that will be used for CAPTCHA detection
                'captcha_sign': 'TEXT',
                # additional HTTP headers in JSON format
                'additional_headers': 'TEXT',
                # IPv4 address of the exit node/relay to use, only required when using Tor
                'exit_node': 'TEXT',
                # only required when using Tor Browser. Possible values: low, medium, or high
                'tbb_security_level': 'TEXT',
                # version of the tool to use, use a single value
                'browser_version': 'TEXT',
                # hash gathered using `captchamonitor md5 -u URL`
                'expected_hash': 'TEXT',
            },
            'failed':
            {
                # unique ID for this table
                'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
                # name of the desired fetcher to use
                'method': 'TEXT',
                # full URL including the http/https prefix
                'url': 'TEXT',
                # CAPTCHA sign that will be used for CAPTCHA detection
                'captcha_sign': 'TEXT',
                # additional HTTP headers in JSON format
                'additional_headers': 'TEXT',
                # IPv4 address of the exit node/relay to use, only required when using Tor
                'exit_node': 'TEXT',
                # only required when using Tor Browser. Possible values: low, medium, or high
                'tbb_security_level': 'TEXT',
                # version of the tool to use, use a single value
                'browser_version': 'TEXT',
                # hash gathered using `captchamonitor md5 -u URL`
                'expected_hash': 'TEXT',
            },
            'relays':
            {
                # unique ID for this table
                'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
                # last modified timestamp of the row
                'last_updated': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
                # BASE64 encoded SHA256 hash
                'fingerprint': 'TEXT UNIQUE',
                # IPv4 address of the relay
                'address': 'TEXT UNIQUE',
                # 1 or 0 if this relay allows IPv4 exits
                'is_ipv4_exiting_allowed': 'TEXT',
                # 1 or 0 if this relay allows IPv6 exits
                'is_ipv6_exiting_allowed': 'TEXT',
                # ISO 3166 alpha-2 country code based on GeoIP
                'country': 'TEXT',
                # continent based on GeoIP, plain English
                'continent': 'TEXT',
                # online or offline
                'status': 'TEXT',
                # list of performed test in {'data':[]} format
                'performed_tests': 'TEXT',
            },
            'urls':
            {
                # unique ID for this table
                'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
                # full URL including the http/https prefix
                'url': 'TEXT',
                # 1 or 0 if the entered URL was a https:// URL
                'is_https': 'TEXT',
                # 1 or 0 if this domain supports IPv4
                'supports_ipv4': 'TEXT',
                # 1 or 0 if this domain supports IPv6
                'supports_ipv6': 'TEXT',
                # hash gathered using `captchamonitor md5 -u URL`
                'hash': 'TEXT',
            },
            'fetchers':
            {
                # unique ID for this table
                'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
                # name of the fetchers coded
                'method': 'TEXT',
                # version(s) of the tool to use, use a JSON list like {"data":[]}
                'versions': 'TEXT',
                # option 1 is preserved for future use
                'option_1': 'TEXT',
                # option 2 is preserved for future use
                'option_2': 'TEXT',
                # option 3 is preserved for future use
                'option_3': 'TEXT',
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
        self.urls_table_name = 'urls'
        self.fetchers_table_name = 'fetchers'

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

    def update_table_entry(self, table, data, identifiers=None):
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

        if identifiers:
            sql_where = ' WHERE'
            sql_where_values = []
            for field in identifiers:
                sql_where += ' %s=? AND' % field
                sql_where_values.append(identifiers[field])

            sql_query = sql_table + sql_set[:-1] + sql_where[:-4]
            data_values = sql_set_values + sql_where_values

        else:
            sql_query = sql_table + sql_set[:-1]
            data_values = sql_set_values

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
