import unittest

import pytest

from captchamonitor.utils.onionoo import Onionoo
from captchamonitor.utils.exceptions import (
    OnionooConnectionError,
    OnionooMissingRelayError,
)


class TestOnionoo(unittest.TestCase):
    def setUp(self):
        self.valid_fingerprint = "A53C46F5B157DD83366D45A8E99A244934A14C46"
        self.invalid_fingerprint = "2222222222222222222222222222222222222222"
        self.exit_ports = [80, 443]

    def test_init(self):
        onionoo = Onionoo(self.valid_fingerprint)

        self.assertEqual(onionoo.fingerprint, self.valid_fingerprint)
        self.assertEqual(onionoo.country.upper(), "US")
        self.assertEqual(onionoo.continent, "America")
        self.assertEqual(onionoo.nickname, "csailmitexit")
        self.assertTrue(onionoo.ipv4_exiting_allowed)
        self.assertFalse(onionoo.ipv6_exiting_allowed)

    def test_invalid_fingerprint(self):
        # Try intializing
        with pytest.raises(OnionooMissingRelayError) as pytest_wrapped_e:
            Onionoo(self.invalid_fingerprint)

        # Check if the exception is correct
        self.assertEqual(pytest_wrapped_e.type, OnionooMissingRelayError)

    def test_is_exiting_allowed(self):
        onionoo = Onionoo(self.valid_fingerprint)

        self.assertFalse(onionoo._Onionoo__is_exiting_allowed({}, self.exit_ports))

        self.assertTrue(
            onionoo._Onionoo__is_exiting_allowed(
                {"reject": ["22", "4661-4666", "6881-6999"]}, self.exit_ports
            )
        )

        self.assertFalse(
            onionoo._Onionoo__is_exiting_allowed(
                {"accept": ["18", "20-30", "1000-2000"]}, self.exit_ports
            )
        )

        self.assertTrue(
            onionoo._Onionoo__is_exiting_allowed({"accept": ["80"]}, self.exit_ports)
        )

        self.assertTrue(
            onionoo._Onionoo__is_exiting_allowed({"reject": ["80"]}, self.exit_ports)
        )

        self.assertFalse(
            onionoo._Onionoo__is_exiting_allowed(
                {"accept": ["100"], "reject": ["80-900"]}, self.exit_ports
            )
        )

    def test_is_in_range(self):
        onionoo = Onionoo(self.valid_fingerprint)

        port_list = ["22", "4661-4666", "6881-6999"]

        self.assertTrue(onionoo._Onionoo__is_in_range(port_list, 22))
        self.assertTrue(onionoo._Onionoo__is_in_range(port_list, 4664))
        self.assertTrue(onionoo._Onionoo__is_in_range(port_list, 6888))

        self.assertFalse(onionoo._Onionoo__is_in_range(port_list, 80))
        self.assertFalse(onionoo._Onionoo__is_in_range(port_list, 443))
        self.assertFalse(onionoo._Onionoo__is_in_range(port_list, 0))
