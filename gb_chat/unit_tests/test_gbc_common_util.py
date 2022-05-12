import socket
import unittest
import sys
import os

sys.path.append(os.path.join(os.getcwd(), '..'))

from unittest import mock
from gb_chat.gbc_common.util import send_message, get_message
from gb_chat.gbc_common.variables import DEFAULT_SERVER_PORT, DEFAULT_SERVER_ADDRESS, MAX_CONNECTIONS


OK_DICT = {'RESPONSE': 200}


class TestUtils(unittest.TestCase):
    server_socket = None
    client_socket = None
    client = None
    client_address = None

    def setUp(self) -> None:
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((DEFAULT_SERVER_ADDRESS, DEFAULT_SERVER_PORT))
        self.server_socket.listen(MAX_CONNECTIONS)

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((DEFAULT_SERVER_ADDRESS, DEFAULT_SERVER_PORT))
        self.client, self.client_address = self.server_socket.accept()

    def tearDown(self) -> None:
        self.client.close()
        self.server_socket.close()
        self.client_socket.close()

    def test_send_message_raises_type_error_on_incorrect_argument(self):
        self.assertRaises(TypeError, send_message, mock.Mock(), 'incorrect message')

    def test_sends_correct_message(self):
        send_message(self.client_socket, OK_DICT)
        response = get_message(self.client)
        self.assertEqual(OK_DICT, response)

    def test_get_message_receives_bytes(self):
        self.assertRaises(ValueError, get_message, mock.Mock())

    def test_get_message_receives_dicts(self):
        self.client_socket.send(bytes([1, 2, 3]))
        self.assertRaises(ValueError, get_message, self.client)



if __name__ == '__main__':
    unittest.main()
