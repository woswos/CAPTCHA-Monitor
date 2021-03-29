class Error(Exception):
    """
    Base class for other exceptions
    """

    pass


class DatabaseInitError(Error):
    """
    Database initialization error
    """

    pass


class ConfigInitError(Error):
    """
    Configuration initialization error
    """

    pass
