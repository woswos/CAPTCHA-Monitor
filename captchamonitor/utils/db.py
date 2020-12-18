import logging
import os

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


class DB:
    def __init__(self):
        """
        The class that communicates with the database directly
        """
        tables = {
            "results": {
                # unique ID for this table
                "id": "BIGSERIAL PRIMARY KEY",
                # the timestamp when the row was inserted
                "timestamp": "TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP",
                # name of the desired fetcher to use
                "method": "TEXT",
                # full URL including the http/https prefix
                "url": "TEXT",
                # CAPTCHA sign that will be used for CAPTCHA detection
                "captcha_sign": "TEXT",
                # 1 if CAPTCHA was found, 0 if CAPTCHA was not found
                "is_captcha_found": "TEXT",
                # 1 if the hash of the received data doesn't match `expected_hash`, otherwise 0
                "is_data_modified": "TEXT",
                # the HTML data gathered as a result of the fetch
                "html_data": "TEXT",
                # the HTTP requests in JSON format made by the fether while fetching the URL
                "requests": "TEXT",
                # IPv4 address of the exit node/relay to use, only required when using Tor
                "exit_node": "TEXT",
                # only required when using Tor Browser. Possible values: low, medium, or high
                "tbb_security_level": "TEXT",
                # version of the tool to use, use a single value
                "browser_version": "TEXT",
                # hash gathered using `captchamonitor md5 -u URL`
                "expected_hash": "TEXT",
                # version of the captchamonitor
                "captchamonitor_version": "TEXT",
            },
            "queue": {
                # unique ID for this table
                "id": "BIGSERIAL PRIMARY KEY",
                # workers use this field for assigning jobs to themselves
                "claimed_by": "TEXT DEFAULT 'None'",
                # name of the desired fetcher to use
                "method": "TEXT",
                # full URL including the http/https prefix
                "url": "TEXT",
                # CAPTCHA sign that will be used for CAPTCHA detection
                "captcha_sign": "TEXT",
                # additional HTTP headers in JSON format
                "additional_headers": "TEXT",
                # IPv4 address of the exit node/relay to use, only required when using Tor
                "exit_node": "TEXT",
                # only required when using Tor Browser. Possible values: low, medium, or high
                "tbb_security_level": "TEXT",
                # version of the tool to use, use a single value
                "browser_version": "TEXT",
                # hash gathered using `captchamonitor md5 -u URL`
                "expected_hash": "TEXT",
            },
            "failed": {
                # unique ID for this table
                "id": "BIGSERIAL PRIMARY KEY",
                # name of the desired fetcher to use
                "method": "TEXT",
                # full URL including the http/https prefix
                "url": "TEXT",
                # CAPTCHA sign that will be used for CAPTCHA detection
                "captcha_sign": "TEXT",
                # additional HTTP headers in JSON format
                "additional_headers": "TEXT",
                # IPv4 address of the exit node/relay to use, only required when using Tor
                "exit_node": "TEXT",
                # only required when using Tor Browser. Possible values: low, medium, or high
                "tbb_security_level": "TEXT",
                # version of the tool to use, use a single value
                "browser_version": "TEXT",
                # hash gathered using `captchamonitor md5 -u URL`
                "expected_hash": "TEXT",
                # details about why this job failed
                "fail_reason": "TEXT",
            },
            "relays": {
                # unique ID for this table
                "id": "BIGSERIAL PRIMARY KEY",
                # last modified timestamp of the row
                "last_updated": "TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP",
                # BASE64 encoded SHA256 hash
                "fingerprint": "TEXT UNIQUE",
                # IPv4 address of the relay
                "address": "TEXT UNIQUE",
                # 1 or 0 if this relay allows IPv4 exits
                "is_ipv4_exiting_allowed": "TEXT",
                # 1 or 0 if this relay allows IPv6 exits
                "is_ipv6_exiting_allowed": "TEXT",
                # ISO 3166 alpha-2 country code based on GeoIP
                "country": "TEXT",
                # continent based on GeoIP, plain English
                "continent": "TEXT",
                # online or offline
                "status": "TEXT",
                # list of performed test in {'data':[]} format
                "performed_tests": "TEXT",
                # nickname of the relay
                "nickname": "TEXT",
                # overall CAPTCHA probability percentage
                "captcha_probability": "TEXT",
                # relay's first seen date
                "first_seen": "TEXT",
                # relay's last seen date
                "last_seen": "TEXT",
                # the Tor version running on the relay
                "version": "TEXT",
                # relay's autonomous system number/code
                "asn": "TEXT",
                # the operating system of the relay
                "platform": "TEXT",
            },
            "urls": {
                # unique ID for this table
                "id": "BIGSERIAL PRIMARY KEY",
                # full URL including the http/https prefix
                "url": "TEXT",
                # 1 or 0 if the entered URL was a https:// URL
                "is_https": "TEXT",
                # 1 or 0 if this domain supports IPv4
                "supports_ipv4": "TEXT",
                # 1 or 0 if this domain supports IPv6
                "supports_ipv6": "TEXT",
                # hash gathered using `captchamonitor md5 -u URL`
                "hash": "TEXT",
                # CAPTCHA sign that will be used for CAPTCHA detection
                "captcha_sign": "TEXT",
                # CDN provider that is fronting the URL (for example Cloudflare)
                "cdn_provider": "TEXT",
                # Comments about the given URL
                "comment": "TEXT",
                # 1 or 0 indicating whether this URL requires multiple HTTP requests to fetch
                "requires_multiple_reqs": "TEXT",
            },
            "fetchers": {
                # unique ID for this table
                "id": "BIGSERIAL PRIMARY KEY",
                # name of the fetchers coded
                "method": "TEXT",
                # version(s) of the tool to use, use a JSON list like {"data":[]}
                "versions": "TEXT",
                # option 1 is preserved for future use
                "option_1": "TEXT",
                # option 2 is preserved for future use
                "option_2": "TEXT",
                # option 3 is preserved for future use
                "option_3": "TEXT",
            },
            "digests": {
                # unique ID for this table
                "id": "BIGSERIAL PRIMARY KEY",
                # the timestamp corresponding to the CAPTCHA rate
                "timestamp": "TIMESTAMPTZ",
                # the Measurement class attribute used to bin the measurements
                "binned_by": "TEXT",
                # the unique key for the current bin
                "bin_key": "TEXT",
                # the function used to decide which measurements to include
                "measurement_filter": "TEXT",
                # the arguments supplied to the filtering function, result of json.dumps()
                "measurement_filter_args": "TEXT",
                # indicates whether exit relay weights were used while taking the average
                "weighted": "BOOLEAN",
                # the sample size for the current bin
                "sample_size": "INT",
                # the calculated CAPTCHA rate for the current bin
                "captcha_rate": "FLOAT",
                # the confidence interval used to calculate the lower and upper bounds, between 0.0 and 1.0
                "confidence_interval": "FLOAT",
                # the mean of the bootstrapped measurements
                "confidence_interval_mean": "FLOAT",
                # the lower bound of confidence interval of the bootstrapped measurements
                "confidence_interval_lower_bound": "FLOAT",
                # the upper bound of confidence interval of the bootstrapped measurements
                "confidence_interval_upper_bound": "FLOAT",
            },
        }

        self.logger = logging.getLogger(__name__)

        try:
            self.host = os.environ["CM_DB_HOST"]
            self.port = os.environ["CM_DB_PORT"]
            self.database = os.environ["CM_DB_NAME"]
            self.user = os.environ["CM_DB_USER"]
            self.password = os.environ["CM_DB_PASS"]

        except Exception as err:
            self.logger.error(
                "Environment variables for the database is not set: %s", err
            )
            return

        self.tables = tables
        self.queue_table_name = "queue"
        self.results_table_name = "results"
        self.failed_table_name = "failed"
        self.relays_table_name = "relays"
        self.urls_table_name = "urls"
        self.fetchers_table_name = "fetchers"
        self.digest_table_name = "digests"

        try:
            # Set database connection
            self.connection = psycopg2.connect(
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port,
                database=self.database,
            )
        except Exception as err:
            self.logger.info(
                "The database does not exist, creating it now: %s", err
            )

            self.check_if_db_exists()

            # Set database connection
            self.connection = psycopg2.connect(
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port,
                database=self.database,
            )

        self.check_if_tables_exists()

    def check_if_db_exists(self):
        """
        Creates the database if the database doesn't exist
        """
        database = self.database

        connection = psycopg2.connect(
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            database="postgres",
        )
        cursor = connection.cursor()

        # This returns false if the database doesn't exist
        sql_check_db = (
            "SELECT EXISTS(SELECT datname FROM pg_catalog.pg_database WHERE datname = '%s')"
            % database
        )
        cursor.execute(sql_check_db)

        if not cursor.fetchone()[0]:
            connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

            create_db = "CREATE DATABASE %s" % database
            cursor.execute(create_db)
            connection.commit()

        cursor.close()
        connection.close()

    def check_if_tables_exists(self):
        """
        Creates the tables if the tables don't exist
        """
        tables = self.tables
        connection = self.connection

        cursor = connection.cursor()

        # Create listed tables
        for table in tables:
            # This returns false if the table doesn't exist
            sql_check_table = (
                "SELECT EXISTS(SELECT * FROM information_schema.tables WHERE table_name = '%s')"
                % table
            )
            cursor.execute(sql_check_table)

            if not cursor.fetchone()[0]:
                # SQL query to create the tables for the first time run
                create_table = "CREATE TABLE %s (" % table

                # Insert field values
                for field in tables[table]:
                    create_table += " %s %s," % (field, tables[table][field])

                # Replace the last comma with ')' to complete the query
                create_table = create_table[:-1] + ")"

                cursor.execute(create_table)
                connection.commit()

        cursor.close()

    def insert_entry_into_table(self, table, data, ignore_existing=False):
        """
        Inserts a given entry into a given table
        """

        table_name = table
        connection = self.connection

        data_fields = ""
        data_q_marks = ""
        data_values = []
        for field in data:
            data_fields += "%s," % field
            data_q_marks += "%s,"
            data_values.append(data[field])

        sql_query = "INSERT INTO %s (%s) VALUES (%s)" % (
            table_name,
            data_fields[:-1],
            data_q_marks[:-1],
        )

        if ignore_existing:
            sql_query = sql_query + " ON CONFLICT DO NOTHING"

        self.logger.debug(sql_query)
        self.logger.debug(data_values)

        cursor = connection.cursor()

        # Try to connect to the database
        try:
            cursor.execute(sql_query, data_values)
            connection.commit()

        except Exception as err:
            self.logger.critical(
                "psycopg2.execute() at insert_entry_into_table() says: %s" % err
            )

        cursor.close()

    def get_table_entries(
        self,
        table,
        columns=["*"],
        identifiers="",
        identifier_operators="",
        after_timestamp="",
        before_timestamp="",
        order_by="",
        order="ASC",
        limit="",
    ):
        """
        Gets the given entries in a given table
        Gets all values if no columns are provided
        Uses the indentifiers for WHERE clause
        """

        table_name = table
        connection = self.connection

        sql_base = "SELECT"

        for column in columns:
            sql_base += " %s," % column

        sql_table = " FROM %s" % table_name

        sql_where = " WHERE"
        for field in identifiers:
            try:
                # Use the defined operator
                sql_where += " %s%s'%s' AND" % (
                    field,
                    identifier_operators[field],
                    identifiers[field],
                )
            except:
                # Fallback to '=' if no operator is defined
                sql_where += " %s='%s' AND" % (field, identifiers[field])

        if identifiers != "":
            sql_query = sql_base[:-1] + sql_table + sql_where[:-4]
        else:
            sql_query = sql_base[:-1] + sql_table

        if before_timestamp != "":
            sql_query = (
                (sql_query + " WHERE ")
                if (not "WHERE" in sql_query)
                else (sql_query + " AND ")
            )

            if after_timestamp != "":
                sql_query += (
                    " timestamp BETWEEN '%s'::timestamp AND '%s'::timestamp "
                    % (after_timestamp, before_timestamp)
                )
            else:
                sql_query += " timestamp < '%s'::timestamp " % before_timestamp

        elif after_timestamp != "":
            sql_query = (
                (sql_query + " WHERE ")
                if (not "WHERE" in sql_query)
                else (sql_query + " AND ")
            )
            sql_query += " timestamp > '%s'::timestamp " % after_timestamp

        if order_by != "":
            sql_query += " ORDER BY %s %s" % (order_by, order)

        if limit != "":
            sql_query += " LIMIT %s" % limit

        self.logger.debug(sql_query)

        cursor = connection.cursor()

        # Try to connect to the database
        try:
            cursor.execute(sql_query)
            connection.commit()

        except Exception as err:
            self.logger.critical(
                "psycopg2.execute() at get_table_entries() says: %s" % err
            )

        result = cursor.fetchall()

        cursor.close()

        final = []
        # Try to place returned data into a dictionary otherwise no data was returned
        try:
            for i in range(len(result)):
                final.append(
                    dict(zip([c[0] for c in cursor.description], result[i]))
                )
        except:
            final = None

        return final

    def count_table_entries(self, table):
        """
        Counts the number of entries in a given table
        """

        table_name = table
        connection = self.connection

        # Prepare the SQL query
        sql_query = "SELECT count(id) FROM %s" % table_name

        self.logger.debug(sql_query)

        cursor = connection.cursor()

        # Try to connect to the database
        try:
            cursor.execute(sql_query)
            connection.commit()

        except Exception as err:
            self.logger.critical(
                "psycopg2.execute() at count_table_entries() says: %s" % err
            )

        result = cursor.fetchone()[0]

        cursor.close()

        return result

    def update_table_entry(self, table, data, identifiers=None):
        """
        Updates a specific table entry with given data using given identifiers
        """

        table_name = table
        connection = self.connection

        sql_table = "UPDATE %s " % table_name

        sql_set = "SET "
        sql_set_values = []
        for field in data:
            sql_set += " %s=" % field
            sql_set += "%s,"  # this is not here for formatting but for sql
            sql_set_values.append(data[field])

        if identifiers:
            sql_where = " WHERE"
            sql_where_values = []
            for field in identifiers:
                sql_where += " %s=" % field
                sql_where += (
                    " %s AND"  # this is not here for formatting but for sql
                )
                sql_where_values.append(identifiers[field])

            sql_query = sql_table + sql_set[:-1] + sql_where[:-4]
            data_values = sql_set_values + sql_where_values

        else:
            sql_query = sql_table + sql_set[:-1]
            data_values = sql_set_values

        self.logger.debug(sql_query)
        self.logger.debug(data_values)

        cursor = connection.cursor()

        # Try to connect to the database
        try:
            cursor.execute(sql_query, data_values)
            connection.commit()

        except Exception as err:
            self.logger.critical(
                "psycopg2.execute() at update_table_entry() says: %s" % err
            )

        cursor.close()

    def remove_table_entry(self, table, identifiers):
        """
        Removes a specific table entry with given identifiers
        """

        table_name = table
        connection = self.connection

        sql_table = "DELETE from %s " % table_name

        sql_where = " WHERE"
        sql_where_values = []
        for field in identifiers:
            sql_where += " %s=" % field
            sql_where += (
                " %s AND"  # this is not here for formatting but for sql
            )
            sql_where_values.append(identifiers[field])

        sql_query = sql_table + sql_where[:-4]
        data_values = sql_where_values

        self.logger.debug(sql_query)
        self.logger.debug(data_values)

        cursor = connection.cursor()

        # Try to connect to the database
        try:
            cursor.execute(sql_query, data_values)
            connection.commit()

        except Exception as err:
            self.logger.critical(
                "psycopg2.execute() at remove_table_entry() says: %s" % err
            )

        cursor.close()

    def claim_first_uncompleted_job(self, worker_id):
        """
        Claims the first uncompleted job in the queue
        """

        table_name = self.queue_table_name
        connection = self.connection

        sql_query = """UPDATE %s SET claimed_by = \'%s\'
                    WHERE id = (SELECT min(id) FROM %s WHERE claimed_by = 'None')""" % (
            table_name,
            worker_id,
            table_name,
        )

        self.logger.debug(sql_query)

        cursor = connection.cursor()

        # Try to connect to the database
        try:
            cursor.execute(sql_query)
            connection.commit()

        except Exception as err:
            self.logger.critical(
                "psycopg2.execute() at claim_first_uncompleted_job() says: %s"
                % err
            )

        cursor.close()
