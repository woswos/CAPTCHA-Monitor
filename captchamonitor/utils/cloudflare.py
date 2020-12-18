import json
import logging
from io import BytesIO

import pycurl


class Cloudflare:
    def __init__(self, cloudflare_email, cloudflare_api_token):
        self.params = {}
        self.credentials = [
            "x-auth-email: {0}".format(cloudflare_email),
            "Authorization: Bearer {0}".format(cloudflare_api_token),
            "Content-Type: application/json",
        ]

        self.logger = logging.getLogger(__name__)

    def set_zone_security_level(self, zone_id, security_level):

        url = "https://api.cloudflare.com/client/v4/zones/{0}/settings/security_level".format(
            zone_id
        )

        # security_level options: essentially_off, low, medium, high, under_attack

        b_obj = BytesIO()
        curl = pycurl.Curl()

        curl.setopt(curl.URL, url)
        curl.setopt(curl.WRITEDATA, b_obj)
        curl.setopt(pycurl.USERAGENT, "curl/7.58.0")
        # curl.setopt(pycurl.VERBOSE, 1)

        curl.setopt(pycurl.HTTPHEADER, self.credentials)

        request_data = str(json.dumps({"value": security_level}))
        curl.setopt(pycurl.CUSTOMREQUEST, "PATCH")
        curl.setopt(pycurl.POSTFIELDS, request_data)

        # Try sending a request to the server and get server's response
        try:
            curl.perform()

        except Exception as err:
            self.logger.error("pycurl.perform() says: %s" % err)
            return -1

        response = b_obj.getvalue().decode("utf8")
        response = json.loads(response)

        # Check if the response was successful
        if str(curl.getinfo(pycurl.RESPONSE_CODE)) != "200":
            curl.close()
            self.logger.error("api call failed")
            return -1

        curl.close()

        self.logger.info(
            "successfully changed the security level to %s" % security_level
        )

    def get_zone_ids(self):

        url = "https://api.cloudflare.com/client/v4/zones"

        b_obj = BytesIO()
        curl = pycurl.Curl()

        curl.setopt(curl.URL, url)
        curl.setopt(curl.WRITEDATA, b_obj)
        curl.setopt(pycurl.USERAGENT, "curl/7.58.0")
        # curl.setopt(pycurl.VERBOSE, 1)

        curl.setopt(pycurl.HTTPHEADER, self.credentials)

        # Try sending a request to the server and get server's response
        try:
            curl.perform()

        except Exception as err:
            self.logger.error("pycurl.perform() says: %s" % err)
            return -1

        response = b_obj.getvalue().decode("utf8")
        response = json.loads(response)

        # Check if the response was successful
        if str(curl.getinfo(pycurl.RESPONSE_CODE)) != "200":
            curl.close()
            self.logger.error("api call failed")
            return -1

        curl.close()

        data = {}
        for zone in response["result"]:
            data[zone["name"]] = zone["id"]

        return data
