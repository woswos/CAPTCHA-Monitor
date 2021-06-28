import pytest

from captchamonitor.utils.exceptions import NoSuchDomain
from captchamonitor.utils.domain_attributes import DomainAttributes


class TestDomainAttributes:
    def test_domain_attributes_init(self):
        domain_attributes = DomainAttributes("google.com")

        assert domain_attributes.supports_ipv4 == True
        assert domain_attributes.supports_ipv6 == True
        assert domain_attributes.supports_http == True
        assert domain_attributes.supports_https == True
        assert domain_attributes.requires_multiple_requests == True

        assert domain_attributes.supports_ftp == False
        assert domain_attributes.gdpr_wait_for_url_change == False

        domain_attributes_2 = DomainAttributes("neverssl.com")

        assert domain_attributes_2.supports_ipv4 == True
        assert domain_attributes_2.supports_http == True
        assert domain_attributes_2.supports_https == True
        assert domain_attributes_2.requires_multiple_requests == True

        assert domain_attributes_2.supports_ipv6 == False
        assert domain_attributes_2.supports_ftp == False
        assert domain_attributes_2.gdpr_wait_for_url_change == False

    def test_non_existing_domain(self):
        with pytest.raises(NoSuchDomain):
            DomainAttributes("lolrandomdomain.randomtld")
