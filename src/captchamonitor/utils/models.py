from datetime import datetime

import pytz
from sqlalchemy import (
    JSON,
    Column,
    String,
    Boolean,
    Integer,
    Unicode,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr, declarative_base

Model = declarative_base()


class BaseModel(Model):  # type: ignore
    """
    Base model for decreasing repetition in all models

    Based on: https://web.archive.org/web/20210329101457/https://dev.to/chidioguejiofor/making-sqlalchemy-models-simpler-by-creating-a-basemodel-3m9c
    """

    __abstract__ = True

    # fmt: off
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(pytz.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    # fmt: on


class MetaData(BaseModel):
    """
    Stores metadata related to CAPTCHA Monitor's progress accross runs
    Uses Key:Value pairs for each metadata
    """

    __tablename__ = "metadata"

    # fmt: off
    key = Column(String, unique=True, nullable=False) # Key for the metadata
    value = Column(String)                            # Value for the metadata
    # fmt: on


class URL(BaseModel):
    """
    Stores list of tracked URLs and metadata related to them
    """

    __tablename__ = "url"

    # fmt: off
    url = Column(String, unique=True, nullable=False)            # Complete URL without protocol
    supports_http = Column(Boolean, nullable=False)              # True or False based on whether the URL supports http protocol
    supports_https = Column(Boolean, nullable=False)             # True or False based on whether the URL supports https protocol
    supports_ftp = Column(Boolean, nullable=False)               # True or False based on whether the URL supports ftp protocol
    supports_ipv4 = Column(Boolean, nullable=False)              # True or False based on whether the URL supports IPv4
    supports_ipv6 = Column(Boolean, nullable=False)              # True or False based on whether the URL supports IPv6
    requires_multiple_requests = Column(Boolean, nullable=False) # True or False based on whether the URL requires multiple HTTP requests to completely fetch
    cdn = Column(String)                                         # CDN provider, if known
    comment = Column(String)                                     # Comments, if there is any
    # fmt: on


class Relay(BaseModel):
    """
    Holds a local mirror of ONIONOO
    """

    __tablename__ = "relay"

    # fmt: off
    fingerprint = Column(String, unique=True, index=True, nullable=False) # BASE64 encoded SHA256 hash
    ipv4_address = Column(String)                                         # IPv4 address of the relay
    ipv6_address = Column(String)                                         # IPv6 address of the relay
    ipv4_exiting_allowed = Column(Boolean)                                # True or False based on whether this relay allows IPv4 exits
    ipv6_exiting_allowed = Column(Boolean)                                # True or False based on whether this relay allows IPv6 exits
    country = Column(String)                                              # ISO 3166 alpha-2 country code based on GeoIP
    country_name = Column(String)                                         # Complete country name based on GeoIP, plain English
    continent = Column(String)                                            # Continent based on GeoIP, plain English
    status = Column(Boolean)                                              # True or False based on whether this relay is online or offline
    nickname = Column(String)                                             # Nickname of the relay
    first_seen = Column(DateTime(timezone=True))                          # Relay's first seen date
    last_seen = Column(DateTime(timezone=True))                           # Relay's last seen date
    version = Column(String)                                              # The Tor version running on the relay
    asn = Column(String)                                                  # Relay's autonomous system number/code
    asn_name = Column(String)                                             # Relay's autonomous system name
    platform = Column(String)                                             # The operating system of the relay
    comment = Column(String)                                              # Comments, if there is any
    # fmt: on


class Fetcher(BaseModel):
    """
    Stores available fetchers
    """

    __tablename__ = "fetcher"

    # fmt: off
    method = Column(String, nullable=False)    # Name of the fetchers coded (Tor Browser, Firefox, Chromium, etc.)
    uses_tor = Column(Boolean, nullable=False) # True or False based on whether this fetcher uses Tor or not
    version = Column(String, nullable=False)   # Version of the tool
    options = Column(JSON)                     # Options, if there is any
    comment = Column(String)                   # Comments, if there is any
    # fmt: on


class FetchBaseModel(BaseModel):
    """
    Base model for fetcher related tables
    """

    __abstract__ = True

    # pylint: disable=E0213
    @declared_attr
    def fetcher_id(cls) -> Column:
        # Name of the desired fetcher to use
        return Column(Integer, ForeignKey("fetcher.id"))

    # pylint: disable=E0213
    @declared_attr
    def url_id(cls) -> Column:
        # Complete URL including the http/https prefix
        return Column(Integer, ForeignKey("url.id"))

    # pylint: disable=E0213
    @declared_attr
    def relay_id(cls) -> Column:
        # Fingerprint exit node/relay to use, only required when using Tor
        return Column(Integer, ForeignKey("relay.id"))

    # fmt: off
    options = Column(JSON)              # Additional options to provide to fetcher in JSON format
    tbb_security_level = Column(String) # Only required when using Tor Browser. Possible values: low, medium, or high
    # fmt: on


class FetchQueue(FetchBaseModel):
    """
    Contains jobs that will be fetched by the fetchers - inherits FetchBaseModel
    """

    __tablename__ = "fetch_queue"

    # fmt: off
    claimed_by = Column(String) # Workers use this field for assigning jobs to themselves
    # fmt: on

    # References to the foreign keys, gives access to these tables
    ref_fetcher = relationship("Fetcher", backref="FetchQueue")
    ref_url = relationship("URL", backref="FetchQueue")
    ref_relay = relationship("Relay", backref="FetchQueue")


class FetchCompleted(FetchBaseModel):
    """
    Contains jobs that are completed - inherits FetchBaseModel
    """

    __tablename__ = "fetch_completed"

    # fmt: off
    captcha_monitor_version = Column(String, nullable=False) # Version of the CAPTCHA Monitor used to do fetching
    html_data = Column(Unicode)                              # The HTML data gathered as a result of the fetch
    http_requests = Column(JSON)                             # The HTTP requests in JSON format made by the fetcher while fetching the URL
    # fmt: on

    # References to the foreign keys, gives access to these tables
    ref_fetcher = relationship("Fetcher", backref="FetchCompleted")
    ref_url = relationship("URL", backref="FetchCompleted")
    ref_relay = relationship("Relay", backref="FetchCompleted")


class FetchFailed(FetchBaseModel):
    """
    Contains jobs that are failed - inherits FetchBaseModel
    """

    __tablename__ = "fetch_failed"

    # fmt: off
    captcha_monitor_version = Column(String, nullable=False) # Version of the CAPTCHA Monitor used to do fetching
    fail_reason = Column(String)                             # The fail reason, if known
    # fmt: on

    # References to the foreign keys, gives access to these tables
    ref_fetcher = relationship("Fetcher", backref="FetchFailed")
    ref_url = relationship("URL", backref="FetchFailed")
    ref_relay = relationship("Relay", backref="FetchFailed")
