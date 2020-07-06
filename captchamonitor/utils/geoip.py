import logging
import maxminddb
import json
import pathlib
import os


class GeoIP:
    def __init__(self):
        GeoLite2_file = '../assests/GeoLite2/GeoLite2-Country.mmdb'
        script_path = pathlib.Path(__file__).parent.absolute()
        db_file = os.path.join(script_path, GeoLite2_file)
        self.reader = maxminddb.open_database(db_file)

    def get_country(self, ip):
        result = self.reader.get(ip)
        return result['country']['iso_code']

    def get_continent(self, ip):
        result = self.reader.get(ip)
        return result['continent']['names']['en']
