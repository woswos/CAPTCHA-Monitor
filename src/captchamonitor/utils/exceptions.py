class Error(Exception):
    """
    Base class for other exceptions
    """


class DatabaseInitError(Error):
    """
    Database initialization error
    """


class ConfigInitError(Error):
    """
    Configuration initialization error
    """


class TorLauncherInitError(Error):
    """
    Tor Launcher initialization error
    """


class StemConnectionInitError(Error):
    """
    Stem cannot connect to the Tor container
    """


class WorkerInitError(Error):
    """
    Worker initialization error
    """


class HarExportExtensionXpiError(Error):
    """
    Provided Har Export Trigger extension is not valid
    """


class FetcherConnectionInitError(Error):
    """
    Fetcher wasn't initialized as expected
    """


class FetcherURLFetchError(Error):
    """
    Fetcher wasn't able to provided URL
    """


class TorBrowserProfileLocationError(Error):
    """
    The provided location is inaccessible or not a valid directory
    """
