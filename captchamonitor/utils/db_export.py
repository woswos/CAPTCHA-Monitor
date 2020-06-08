import sqlite3
import logging
import os

logger = logging.getLogger(__name__)


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def export(path):
    '''
    Export the SQlite database to JSON file

    Original code taken from https://github.com/Austyns/sqlite-to-json-python
    '''

    db_file = os.environ['CM_DB_FILE_PATH']
    db_export_location = path

    if not os.path.exists(db_export_location):
        os.makedirs(db_export_location)

    # connect to the SQlite databases
    connection = sqlite3.connect(db_file)
    connection.row_factory = dict_factory

    cursor = connection.cursor()

    # select all the tables from the database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    # for each of the bables , select all the records from the table
    for table_name in tables:
        conn = sqlite3.connect(db_file)
        conn.row_factory = dict_factory

        cur1 = conn.cursor()

        cur1.execute("SELECT * FROM " + table_name['name'])

        # fetch all or one we'll go for all.
        results = cur1.fetchall()

        # generate and save JSON files with the table name for each of the database tables
        export_file_name = os.path.join(db_export_location, (table_name['name']+'.json'))
        with open(export_file_name, 'a') as the_file:
            the_file.write(format(results).replace(" u'", "'").replace('"', "\""))

    connection.close()
