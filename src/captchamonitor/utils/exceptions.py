class Error(Exception):
    """
    Base class for other exceptions
    """


class DatabaseInitError(Error):
    def __str__(self):
        return "Database initialization error"


class ConfigInitError(Error):
    def __str__(self):
        return "Configuration initialization error"


class TorLauncherInitError(Error):
    def __str__(self):
        return "Tor Launcher initialization error"


class StemConnectionInitError(Error):
    def __str__(self):
        return "Stem cannot connect to the Tor container"


class StemDescriptorUnavailableError(Error):
    def __str__(self):
        return "Stem cannot get relay descriptors"


class WorkerInitError(Error):
    def __str__(self):
        return "Worker initialization error"


class HarExportExtensionXpiError(Error):
    def __str__(self):
        return "Provided Har Export Trigger extension is not valid"


class FetcherConnectionInitError(Error):
    def __str__(self):
        return "Fetcher wasn't initialized as expected"


class FetcherURLFetchError(Error):
    def __str__(self):
        return "Fetcher wasn't able to provided URL"


class TorBrowserProfileLocationError(Error):
    def __str__(self):
        return "The provided location is inaccessible or not a valid directory"


class FetcherNotFound(Error):
    def __str__(self):
        return "The provided fetcher method is not available"
