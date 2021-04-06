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


class FetcherConnectionInitError(Error):
    """
    Fetcher wasn't initialized as expected
    """


class TorBrowserProfileLocationError(Error):
    """
    The provided location is inaccessible or not a valid directory
    """
