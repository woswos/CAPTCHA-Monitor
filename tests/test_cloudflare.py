import pytest
import pycurl
from io import BytesIO
import json
from captchamonitor.utils.cloudflare import Cloudflare


email = ''
api_token = ''
domain = ''
security_level = 'medium'
# security_level options: essentially_off, low, medium, high, under_attack

"""
def test_cloudflare_security_level_change():
    # Change it first
    cloudflare = Cloudflare(email, api_token)
    zone_ids = cloudflare.get_zone_ids()
    cloudflare.set_zone_security_level(zone_ids[domain], security_level)

    # Check it now
    credentials = ['x-auth-email: {0}'.format(email),
                   'Authorization: Bearer {0}'.format(api_token),
                   'Content-Type: application/json']

    url = 'https://api.cloudflare.com/client/v4/zones/{0}/settings/security_level'.format(
        zone_ids[domain])

    b_obj = BytesIO()
    curl = pycurl.Curl()

    curl.setopt(curl.URL, url)
    curl.setopt(curl.WRITEDATA, b_obj)
    curl.setopt(pycurl.USERAGENT, 'curl/7.58.0')
    curl.setopt(pycurl.HTTPHEADER, credentials)
    curl.perform()

    response = b_obj.getvalue().decode('utf8')
    response = json.loads(response)

    assert response['result']['value'] == security_level
"""
