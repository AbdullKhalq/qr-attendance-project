import socket
import unittest
from unittest.mock import MagicMock, patch

from config import default_public_base_url, discover_host_ipv4


class HostAddressTests(unittest.TestCase):
    @patch("config.socket.socket")
    def test_active_route_address_is_used(self, socket_factory: MagicMock) -> None:
        connection = socket_factory.return_value.__enter__.return_value
        connection.getsockname.return_value = ("192.168.1.45", 54321)

        self.assertEqual(discover_host_ipv4(), "192.168.1.45")
        connection.connect.assert_called_once_with(("8.8.8.8", 80))

    @patch("config.socket.getaddrinfo")
    @patch("config.socket.socket")
    def test_hostname_address_is_the_fallback(
        self,
        socket_factory: MagicMock,
        getaddrinfo: MagicMock,
    ) -> None:
        socket_factory.return_value.__enter__.return_value.connect.side_effect = OSError
        getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_DGRAM, 17, "", ("127.0.0.1", 0)),
            (socket.AF_INET, socket.SOCK_DGRAM, 17, "", ("10.0.0.20", 0)),
        ]

        self.assertEqual(discover_host_ipv4(), "10.0.0.20")

    @patch("config.discover_host_ipv4", return_value="192.168.0.9")
    def test_default_url_contains_host_ip(self, _discover: MagicMock) -> None:
        self.assertEqual(default_public_base_url(), "http://192.168.0.9:5000")


if __name__ == "__main__":
    unittest.main()
