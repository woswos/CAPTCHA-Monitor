import unittest

from captchamonitor.utils.exceptions import NoSuchDomain
from captchamonitor.utils.domain_attributes import DomainAttributes


class TestDomainAttributes(unittest.TestCase):
    def test_domain_attributes_init(self):
        domain_attributes = DomainAttributes("google.com")

        self.assertTrue(domain_attributes.supports_ipv4)
        self.assertTrue(domain_attributes.supports_ipv6)
        self.assertTrue(domain_attributes.supports_http)
        self.assertTrue(domain_attributes.supports_https)
        self.assertTrue(domain_attributes.requires_multiple_requests)

        self.assertFalse(domain_attributes.supports_ftp)
        self.assertFalse(domain_attributes.gdpr_wait_for_url_change)

        domain_attributes_2 = DomainAttributes("neverssl.com")

        self.assertTrue(domain_attributes_2.supports_ipv4)
        self.assertTrue(domain_attributes_2.supports_http)
        self.assertTrue(domain_attributes_2.supports_https)
        self.assertTrue(domain_attributes_2.requires_multiple_requests)

        self.assertFalse(domain_attributes_2.supports_ipv6)
        self.assertFalse(domain_attributes_2.supports_ftp)
        self.assertFalse(domain_attributes_2.gdpr_wait_for_url_change)

    def test_non_existing_domain(self):
        with self.assertRaises(NoSuchDomain):
            DomainAttributes("lolrandomdomain.randomtld")
