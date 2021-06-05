import unittest

from captchamonitor.utils.onionoo import Onionoo


class TestOnionoo(unittest.TestCase):
    def setUp(self):
        self.csailmitexit_fpr = "A53C46F5B157DD83366D45A8E99A244934A14C46"
        self.csailmitnoexit_fpr = "9715C81BA8C5B0C698882035F75C67D6D643DBE3"
        self.exit_ports = [80, 443]

    def test_onionoo_init(self):
        onionoo = Onionoo([self.csailmitexit_fpr])
        relay = onionoo.relay_entries[0]

        self.assertEqual(relay.fingerprint, self.csailmitexit_fpr)
        self.assertEqual(relay.country.upper(), "US")
        self.assertEqual(relay.continent, "America")
        self.assertEqual(relay.nickname, "csailmitexit")
        self.assertTrue(relay.ipv4_exiting_allowed)
        self.assertFalse(relay.ipv6_exiting_allowed)

    def test_onionoo_init_multiple_relays(self):
        onionoo = Onionoo([self.csailmitexit_fpr, self.csailmitnoexit_fpr])

        self.assertEqual(len(onionoo.relay_entries), 2)

    def test_is_exiting_allowed(self):
        onionoo = Onionoo([self.csailmitexit_fpr])

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
        onionoo = Onionoo([self.csailmitexit_fpr])

        port_list = ["22", "4661-4666", "6881-6999"]

        self.assertTrue(onionoo._Onionoo__is_in_range(port_list, 22))
        self.assertTrue(onionoo._Onionoo__is_in_range(port_list, 4664))
        self.assertTrue(onionoo._Onionoo__is_in_range(port_list, 6888))

        self.assertFalse(onionoo._Onionoo__is_in_range(port_list, 80))
        self.assertFalse(onionoo._Onionoo__is_in_range(port_list, 443))
        self.assertFalse(onionoo._Onionoo__is_in_range(port_list, 0))
