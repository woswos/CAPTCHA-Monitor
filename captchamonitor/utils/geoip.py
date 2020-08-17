import logging
import maxminddb
import json
import pathlib
import os


class GeoIP:
    """
    This class communicates with the MaxMind GeoLite2-Country database to convert
    IP addresses to country and continent names
    """

    def __init__(self):
        """
        Constructor method
        """

        GeoLite2_file = '../assests/GeoLite2/GeoLite2-Country.mmdb'
        script_path = pathlib.Path(__file__).parent.absolute()
        db_file = os.path.join(script_path, GeoLite2_file)
        self.reader = maxminddb.open_database(db_file)

    def get_country(self, ip):
        """
        Converts a given IP address to 2-letter ISO country code

        :param ip: the desired IPv4 or IPv6 address for conversion
        :type ip: str

        :returns: the 2-letter ISO country code [returns 'ZZ' for unknown IP addresses]
        :rtype: str
        """
        result = self.reader.get(ip)

        try:
            return result['country']['iso_code']

        except:
            return 'ZZ'

    def get_continent(self, ip):
        """
        Converts a given IP address to human readable continent names

        :param ip: the desired IPv4 or IPv6 address for conversion
        :type ip: str

        :returns: the continent name [returns 'unknown' for unknown IP addresses]
        :rtype: str
        """
        result = self.reader.get(ip)

        try:
            return result['continent']['names']['en']

        except:
            return 'unknown'
