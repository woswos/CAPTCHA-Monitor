from captchamonitor.utils.onionoo import Onionoo


class TestOnionoo:
    @classmethod
    def setup_class(cls):
        cls.csailmitexit_fpr = "A53C46F5B157DD83366D45A8E99A244934A14C46"
        cls.csailmitnoexit_fpr = "9715C81BA8C5B0C698882035F75C67D6D643DBE3"
        cls.exit_ports = [80, 443]

    def test_onionoo_init(self):
        onionoo = Onionoo([self.csailmitexit_fpr])
        relay = onionoo.relay_entries[0]

        assert relay.fingerprint == self.csailmitexit_fpr
        assert relay.country.upper() == "US"
        assert relay.continent == "America"
        assert relay.nickname == "csailmitexit"
        assert relay.ipv4_exiting_allowed == True
        assert relay.ipv6_exiting_allowed == False

    def test_onionoo_init_multiple_relays(self):
        onionoo = Onionoo([self.csailmitexit_fpr, self.csailmitnoexit_fpr])

        assert len(onionoo.relay_entries) == 2

    def test_is_exiting_allowed(self):
        onionoo = Onionoo([self.csailmitexit_fpr])

        assert onionoo._Onionoo__is_exiting_allowed({}, self.exit_ports) == False

        assert (
            onionoo._Onionoo__is_exiting_allowed(
                {"reject": ["22", "4661-4666", "6881-6999"]}, self.exit_ports
            )
            == True
        )

        assert (
            onionoo._Onionoo__is_exiting_allowed(
                {"accept": ["18", "20-30", "1000-2000"]}, self.exit_ports
            )
            == False
        )

        assert (
            onionoo._Onionoo__is_exiting_allowed({"accept": ["80"]}, self.exit_ports)
            == True
        )

        assert (
            onionoo._Onionoo__is_exiting_allowed({"reject": ["80"]}, self.exit_ports)
            == True
        )

        assert (
            onionoo._Onionoo__is_exiting_allowed(
                {"accept": ["100"], "reject": ["80-900"]}, self.exit_ports
            )
            == False
        )

    def test_is_in_range(self):
        onionoo = Onionoo([self.csailmitexit_fpr])

        port_list = ["22", "4661-4666", "6881-6999"]

        assert onionoo._Onionoo__is_in_range(port_list, 22) == True
        assert onionoo._Onionoo__is_in_range(port_list, 4664) == True
        assert onionoo._Onionoo__is_in_range(port_list, 6888) == True

        assert onionoo._Onionoo__is_in_range(port_list, 80) == False
        assert onionoo._Onionoo__is_in_range(port_list, 443) == False
        assert onionoo._Onionoo__is_in_range(port_list, 0) == False
