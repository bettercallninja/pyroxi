import unittest
from pyroxi.core.connection import Connection
from pyroxi.exceptions import ProxyConnectionError

class TestConnection(unittest.TestCase):

    def setUp(self):
        self.connection = Connection()

    def test_connect(self):
        self.connection.set_proxy('http://example.com:8080')
        self.assertTrue(self.connection.connect())
        self.assertTrue(self.connection.is_connected())

    def test_disconnect(self):
        self.connection.set_proxy('http://example.com:8080')
        self.connection.connect()
        self.connection.disconnect()
        self.assertFalse(self.connection.is_connected())

    def test_connect_invalid_proxy(self):
        self.connection.set_proxy('invalid_proxy')
        with self.assertRaises(ProxyConnectionError):
            self.connection.connect()

    def tearDown(self):
        if self.connection.is_connected():
            self.connection.disconnect()

if __name__ == '__main__':
    unittest.main()