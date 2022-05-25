import unittest
import sys
import os

sys.path.append(os.path.join(os.getcwd(), '..'))

from unittest.mock import patch

from server import parse_arguments, process_client_message
from gbc_common.variables import *

MOCKED_ADDRESS = '192.168.0.1'
ERROR_RESPONSE = {RESPONSE: 400, ERROR: 'Bad request'}
OK_RESPONSE = {RESPONSE: 200}


class TestServer(unittest.TestCase):
    @patch.object(sys, 'argv', ['some_file.py'])
    def test_parse_arguments_empty_arguments(self):
        args = parse_arguments()
        self.assertEqual(args.address, DEFAULT_SERVER_LISTEN_ADDRESS)
        self.assertEqual(args.port, DEFAULT_SERVER_PORT)

    @patch.object(sys, 'argv', ['some_file.py', '-a', MOCKED_ADDRESS, '-p', '111'])
    def test_parse_arguments_address_low_port(self):
        self.assertRaises(ValueError, parse_arguments)

    @patch.object(sys, 'argv', ['some_file.py', '-a', MOCKED_ADDRESS, '-p', '111111'])
    def test_parse_arguments_address_high_port(self):
        self.assertRaises(ValueError, parse_arguments)

    def test_process_client_correct_request(self):
        self.assertEqual(OK_RESPONSE,
                         process_client_message({ACTION: PRESENCE, TIME: '111', USER: {ACCOUNT_NAME: 'Guest'}}))

    def test_process_client_message_empty_request(self):
        self.assertEqual(ERROR_RESPONSE, process_client_message({}))

    def test_process_client_message_wrong_action(self):
        self.assertEqual(ERROR_RESPONSE, process_client_message(
            {ACTION: 'Oops', TIME: '111', USER: {ACCOUNT_NAME: 'Guest'}}))


if __name__ == '__main__':
    unittest.main()
