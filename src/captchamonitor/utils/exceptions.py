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
