class Error(Exception):
    """
    Base class for other exceptions
    """


class DatabaseInitError(Error):
    def __str__(self) -> str:
        return "DatabaseInitError: Database initialization error"


class ConfigInitError(Error):
    def __str__(self) -> str:
        return "ConfigInitError: Configuration initialization error"


class TorLauncherInitError(Error):
    def __str__(self) -> str:
        return "TorLauncherInitError: Tor Launcher initialization error"


class OnionooConnectionError(Error):
    def __str__(self) -> str:
        return "OnionooConnectionError: Onionoo API connection error"


class OnionooMissingRelayError(Error):
    def __str__(self) -> str:
        return "OnionooMissingRelayError: Given relay does not exist on Onionoo yet"


class CollectorDownloadError(Error):
    def __str__(self) -> str:
        return "CollectorDownloadError: Cannot download requested consensus file from Collector"


class CollectorConnectionError(Error):
    def __str__(self) -> str:
        return "CollectorConnectionError: Cannot connect to Collector API"


class ConsensusParserFileNotFoundError(Error):
    def __str__(self) -> str:
        return "ConsensusParserFileNotFoundError: Given consensus file doesn't exist"


class ConsensusParserInvalidDocument(Error):
    def __str__(self) -> str:
        return "ConsensusParserInvalidDocument: Given consensus file is not valid"


class StemConnectionInitError(Error):
    def __str__(self) -> str:
        return "StemConnectionInitError: Stem cannot connect to the Tor container"


class StemDescriptorUnavailableError(Error):
    def __str__(self) -> str:
        return "StemDescriptorUnavailableError: Stem cannot get relay descriptors"


class WorkerInitError(Error):
    def __str__(self) -> str:
        return "WorkerInitError: Worker initialization error"


class HarExportExtensionError(Error):
    def __str__(self) -> str:
        return "HarExportExtensionError: Provided Har Export Trigger extension is not valid"


class FetcherConnectionInitError(Error):
    def __str__(self) -> str:
        return "FetcherConnectionInitError: Fetcher wasn't initialized as expected"


class FetcherURLFetchError(Error):
    def __str__(self) -> str:
        return "FetcherURLFetchError: Fetcher wasn't able to process the provided URL"


class TorBrowserProfileLocationError(Error):
    def __str__(self) -> str:
        return "TorBrowserProfileLocationError: The provided location is inaccessible or not a valid directory"


class FetcherNotFound(Error):
    def __str__(self) -> str:
        return "FetcherNotFound: The provided fetcher method is not available"


class WebsiteParserFetchError(Error):
    def __str__(self) -> str:
        return "WebsiteParserFetchError: Cannot fetch the target website"


class WebsiteParserParseError(Error):
    def __str__(self) -> str:
        return "WebsiteParserParseError: Cannot parse the website as expected, probably the website layout has changed"
