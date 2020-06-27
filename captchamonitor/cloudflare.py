import logging
import sys
from captchamonitor.utils.cloudflare import Cloudflare

def cloudflare(args):
    logger = logging.getLogger(__name__)

    if args.verbose:
        logging.getLogger('captchamonitor').setLevel(logging.DEBUG)

    email = args.email
    api_token = args.token
    domain = args.domain
    security_level = args.security_level

    cloudflare = Cloudflare(email, api_token)
    zone_ids = cloudflare.get_zone_ids()
    cloudflare.set_zone_security_level(zone_ids[domain], security_level)

    sys.exit()
