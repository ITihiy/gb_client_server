import argparse
import logging
import os
import socket
import sys
import time
from threading import Thread

from gbc_common.util import get_message, send_message
from gbc_common.variables import *

sys.path.append(os.path.join(os.getcwd(), '..'))

logger = logging.getLogger('client_logger')


def parse_arguments():
    parser = argparse.ArgumentParser(description='GB CLI chat client')
    parser.add_argument('address', nargs='?', default=DEFAULT_SERVER_ADDRESS)
    parser.add_argument('port', nargs='?', default=DEFAULT_SERVER_PORT, type=int)
    parser.add_argument('--name', '-n', nargs='?', type=str)
    args = parser.parse_args()
    if args.port < 1024 or args.port > 65355:
        logger.critical(f'client called with incorrect port number: {args.port}')
        raise ValueError('Invalid port number. Should be in range 1025-65535')
    return args


class GBChatClient:
    def __init__(self, server_address, server_port, user_name):
        self.server_address = server_address
        self.server_port = server_port
        self.user_name = user_name
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.server_address, self.server_port))

    def create_presence_message(self):
        logger.info(f'presence message with account {self.user_name} created')
        return {
            ACTION: PRESENCE,
            TIME: time.time(),
            USER: {
                ACCOUNT_NAME: self.user_name,
            },
        }

    def create_exit_message(self):
        logger.info(f'exit message with account {self.user_name} created')
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.user_name,
        }

    def create_text_message(self):
        receiver = input('Please input user name to send message: ')
        message = input('Please input message to send: ')
        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.user_name,
            DESTINATION: receiver,
            TIME: time.time(),
            MESSAGE_TEXT: message,
        }
        logger.debug(f'Message dict formed: {message_dict}')
        try:
            send_message(self.sock, message_dict)
        except Exception as e:
            logger.critical(f'Could not send message from {self.user_name} to {receiver}. Error: {e}')
            sys.exit(1)

    @staticmethod
    def process_presence_answer(message):
        if RESPONSE in message and message[RESPONSE] == 200:
            return '200: OK'
        elif RESPONSE in message and message[RESPONSE] == 400:
            raise ValueError(f'400: {message[ERROR]}')
        raise ValueError

    def main_loop(self):
        logger.info(
            f'Client started with parameters: {self.server_address}:{self.server_port} with'
            f' {self.user_name} user name.')
        try:
            send_message(self.sock, self.create_presence_message())
            answer = self.process_presence_answer(get_message(self.sock))
            logger.info(
                f'Successfully connected to server: {self.server_address}:{self.server_port}. Answer was: {answer}')
        except ValueError as err:
            logger.critical(f'Failed connecting to server: {err}')
            sys.exit(1)
        print(f'{self.user_name} successfully logged in to server {self.server_address}:{self.server_port}')

        receiver = GBChatClientReceiverThread(self.sock, self.user_name)
        sender = GBChatClientSenderThread(self)

        receiver.start()
        sender.start()

        logger.info(f'Client {self.user_name} had successfully started')

        while receiver.is_alive() and sender.is_alive():
            time.sleep(1)


class GBChatClientReceiverThread(Thread):
    def __init__(self, server_socket, user_name):
        super().__init__()
        self.server_socket = server_socket
        self.user_name = user_name

    def run(self) -> None:
        while True:
            try:
                message = get_message(self.server_socket)
                if ACTION in message and message[ACTION] == MESSAGE and \
                        SENDER in message and DESTINATION in message and MESSAGE_TEXT in message and \
                        message[DESTINATION] == self.user_name:
                    print(f'Received message from {message[SENDER]}: {message[MESSAGE_TEXT]}')
                else:
                    logger.error(f'Incorrect message received: {message}')
            except Exception as e:
                logger.critical(f'{e} while receiving message. Quitting')
                sys.exit(1)


class GBChatClientSenderThread(Thread):
    def __init__(self, client: GBChatClient):
        super().__init__()
        self.client = client

    def run(self):
        print('Available commands: message, help, exit')
        while True:
            command = input('Please input a command: ')
            if command == 'message':
                self.client.create_text_message()
            elif command == 'help':
                print('Available commands: message, help, exit')
            elif command == 'exit':
                send_message(self.client.sock, self.client.create_exit_message())
                print('Closing client. Bye.')
                time.sleep(0.5)
                break
            else:
                print('Incorrect command')


def main():
    arguments = parse_arguments()
    client = GBChatClient(arguments.address, arguments.port, arguments.name)
    client.main_loop()


if __name__ == '__main__':
    main()
