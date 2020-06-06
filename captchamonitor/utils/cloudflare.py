import logging
import pycurl
from io import BytesIO
import json
try:
    import configparser
except ImportError:
    import ConfigParser as configparser

logger = logging.getLogger(__name__)


class Cloudflare:
    def __init__(self, config_file):
        self.params = {}
        config = configparser.ConfigParser()
        config.read(config_file)
        cloudflare_email = config['CLOUDFLARE']['cloudflare_email']
        cloudflare_api_token = config['CLOUDFLARE']['cloudflare_api_token']
        self.credentials = ['x-auth-email: {0}'.format(cloudflare_email),
                            'Authorization: Bearer {0}'.format(cloudflare_api_token),
                            'Content-Type: application/json']

    def set_zone_security_level(self, zone_id, security_level):

        url = 'https://api.cloudflare.com/client/v4/zones/{0}/settings/security_level'.format(
            zone_id)

        # security_level options: essentially_off, low, medium, high, under_attack

        b_obj = BytesIO()
        curl = pycurl.Curl()

        curl.setopt(curl.URL, url)
        curl.setopt(curl.WRITEDATA, b_obj)
        curl.setopt(pycurl.USERAGENT, 'curl/7.58.0')
        #curl.setopt(pycurl.VERBOSE, 1)

        curl.setopt(pycurl.HTTPHEADER, self.credentials)

        request_data = str(json.dumps({"value": security_level}))
        curl.setopt(pycurl.CUSTOMREQUEST, "PATCH")
        curl.setopt(pycurl.POSTFIELDS, request_data)

        # Try sending a request to the server and get server's response
        try:
            curl.perform()

        except Exception as err:
            logger.error('pycurl.perform() says: %s' % err)
            return -1

        response = b_obj.getvalue().decode('utf8')
        response = json.loads(response)

        # Check if the response was successful
        if str(curl.getinfo(pycurl.RESPONSE_CODE)) != '200':
            curl.close()
            logger.error('api call failed')
            return -1

        curl.close()

        logger.error('successfully changed the security level to %s' % security_level)

    def get_zone_ids(self):

        url = 'https://api.cloudflare.com/client/v4/zones'

        b_obj = BytesIO()
        curl = pycurl.Curl()

        curl.setopt(curl.URL, url)
        curl.setopt(curl.WRITEDATA, b_obj)
        curl.setopt(pycurl.USERAGENT, 'curl/7.58.0')
        #curl.setopt(pycurl.VERBOSE, 1)

        curl.setopt(pycurl.HTTPHEADER, self.credentials)

        # Try sending a request to the server and get server's response
        try:
            curl.perform()

        except Exception as err:
            logger.error('pycurl.perform() says: %s' % err)
            return -1

        response = b_obj.getvalue().decode('utf8')
        response = json.loads(response)

        # Check if the response was successful
        if str(curl.getinfo(pycurl.RESPONSE_CODE)) != '200':
            curl.close()
            logger.error('api call failed')
            return -1

        curl.close()

        data = {}
        for zone in response['result']:
            data[zone['name']] = zone['id']

        return data
