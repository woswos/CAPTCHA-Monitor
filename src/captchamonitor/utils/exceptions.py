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
