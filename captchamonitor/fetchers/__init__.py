from .tor_browser import fetch_via_tor_browser as tor_browser
from .chromium import fetch_via_chromium as chromium
from .chromium_over_tor import fetch_via_chromium_over_tor as chromium_over_tor
from .firefox import fetch_via_firefox as firefox
from .firefox_over_tor import fetch_via_firefox_over_tor as firefox_over_tor
from .requests import fetch_via_requests as requests
from .requests_over_tor import fetch_via_requests_over_tor as requests_over_tor
from .curl import fetch_via_curl as curl
from .curl_over_tor import fetch_via_curl_over_tor as curl_over_tor
from .brave import fetch_via_brave as brave
from .brave_over_tor import fetch_via_brave_over_tor as brave_over_tor
