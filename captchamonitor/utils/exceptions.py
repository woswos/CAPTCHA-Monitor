class Error(Exception):
    """Base class for other exceptions"""

    pass


class BrowserInitErr(Error):
    """Browser initialization error"""

    pass


class WebDriverGetErr(Error):
    """Error while using webdriver.get()"""

    pass


class HTTPHeaderLiveParseErr(Error):
    """HTTP-Header-Live extension had problem while parsing the headers"""

    pass


class HTTPHeaderLiveCaptureErr(Error):
    """Couldn't capture headers from HTTP-Header-Live extension export file"""

    pass


class MissingEnvVar(Error):
    """There are required but missing environment variables"""

    pass
