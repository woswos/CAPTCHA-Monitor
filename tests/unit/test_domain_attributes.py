# pylint: disable=C0115,C0116,W0212

import pytest

from captchamonitor.utils.exceptions import NoSuchDomain
from captchamonitor.utils.domain_attributes import DomainAttributes


class TestDomainAttributes:
    @staticmethod
    def test_domain_attributes_init():
        domain_attributes = DomainAttributes("google.com")

        assert domain_attributes.supports_ipv4 is True
        assert domain_attributes.supports_ipv6 is True
        assert domain_attributes.supports_http is True
        assert domain_attributes.supports_https is True
        assert domain_attributes.requires_multiple_requests is True

        assert domain_attributes.supports_ftp is False

        domain_attributes_2 = DomainAttributes("neverssl.com")

        assert domain_attributes_2.supports_ipv4 is True
        assert domain_attributes_2.supports_http is True
        assert domain_attributes_2.supports_https is True
        assert domain_attributes_2.requires_multiple_requests is True

        assert domain_attributes_2.supports_ipv6 is False
        assert domain_attributes_2.supports_ftp is False

    @staticmethod
    def test_non_existing_domain():
        with pytest.raises(NoSuchDomain):
            DomainAttributes("lolrandomdomain.randomtld")
