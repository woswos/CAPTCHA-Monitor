class Error(Exception):
    """
    Base class for other exceptions
    """


class DatabaseInitError(Error):
    def __str__(self):
        return "DatabaseInitError: Database initialization error"


class ConfigInitError(Error):
    def __str__(self):
        return "ConfigInitError: Configuration initialization error"


class TorLauncherInitError(Error):
    def __str__(self):
        return "TorLauncherInitError: Tor Launcher initialization error"


class StemConnectionInitError(Error):
    def __str__(self):
        return "StemConnectionInitError: Stem cannot connect to the Tor container"


class StemDescriptorUnavailableError(Error):
    def __str__(self):
        return "StemDescriptorUnavailableError: Stem cannot get relay descriptors"


class WorkerInitError(Error):
    def __str__(self):
        return "WorkerInitError: Worker initialization error"


class HarExportExtensionXpiError(Error):
    def __str__(self):
        return "HarExportExtensionXpiError: Provided Har Export Trigger extension is not valid"


class FetcherConnectionInitError(Error):
    def __str__(self):
        return "FetcherConnectionInitError: Fetcher wasn't initialized as expected"


class FetcherURLFetchError(Error):
    def __str__(self):
        return "FetcherURLFetchError: Fetcher wasn't able to process the provided URL"


class TorBrowserProfileLocationError(Error):
    def __str__(self):
        return "TorBrowserProfileLocationError: The provided location is inaccessible or not a valid directory"


class FetcherNotFound(Error):
    def __str__(self):
        return "FetcherNotFound: The provided fetcher method is not available"
