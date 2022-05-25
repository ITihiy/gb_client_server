import unittest
import sys
import os

sys.path.append(os.path.join(os.getcwd(), '..'))

from unittest.mock import patch

from client import parse_arguments, create_presence_message, process_answer
from gbc_common.variables import *

MOCKED_ADDRESS = '192.168.0.1'
MOCKED_PORT = '5555'
MOCKED_NAME = 'mock'


class TestClient(unittest.TestCase):
    @patch.object(sys, 'argv', ['some_file.py'])
    def test_parse_arguments_empty_arguments(self):
        args = parse_arguments()
        self.assertEqual(args.address, DEFAULT_SERVER_ADDRESS)
        self.assertEqual(args.port, DEFAULT_SERVER_PORT)

    @patch.object(sys, 'argv', ['some_file.py', MOCKED_ADDRESS])
    def test_parse_arguments_address_no_port(self):
        args = parse_arguments()
        self.assertEqual(args.address, MOCKED_ADDRESS)
        self.assertEqual(args.port, DEFAULT_SERVER_PORT)

    @patch.object(sys, 'argv', ['some_file.py', MOCKED_ADDRESS, MOCKED_PORT])
    def test_parse_arguments_address_and_port(self):
        args = parse_arguments()
        self.assertEqual(args.address, MOCKED_ADDRESS)
        self.assertEqual(args.port, int(MOCKED_PORT))

    @patch.object(sys, 'argv', ['some_file.py', MOCKED_ADDRESS, '111'])
    def test_parse_arguments_address_low_port(self):
        self.assertRaises(ValueError, parse_arguments)

    @patch.object(sys, 'argv', ['some_file.py', MOCKED_ADDRESS, '111111'])
    def test_parse_arguments_address_high_port(self):
        self.assertRaises(ValueError, parse_arguments)

    def test_create_presence_message_default_argument(self):
        message = create_presence_message()
        self.assertEqual('Guest', message[USER][ACCOUNT_NAME])

    def test_create_presence_message_custom_argument(self):
        message = create_presence_message(MOCKED_NAME)
        self.assertEqual(MOCKED_NAME, message[USER][ACCOUNT_NAME])

    def test_process_answer_incorrect_message(self):
        self.assertRaises(ValueError, process_answer, 'Hello there')

    def test_process_answer_correct_message(self):
        reply = process_answer({'response': 200})
        self.assertEqual('200: OK', reply)

    def test_process_answer_message_with_error(self):
        reply = process_answer({'response': 300, 'error': 'something went wrong'})
        self.assertIn('400:', reply)


if __name__ == '__main__':
    unittest.main()
