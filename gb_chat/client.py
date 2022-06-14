import argparse
import logging
import os
import socket
import sys
import time
from threading import Thread, Lock

from client_storage import ClientDBStorage
from descrs import PortDescriptor
from errors import ServerError
from gbc_common.util import get_message, send_message
from gbc_common.variables import *
from metaclasses import ClientVerifier

sys.path.append(os.path.join(os.getcwd(), '..'))

SOCKET_TIMEOUT = 1

logger = logging.getLogger('client_logger')
socket_lock = Lock()
db_lock = Lock()


def parse_arguments():
    parser = argparse.ArgumentParser(description='GB CLI chat client')
    parser.add_argument('address', nargs='?', default=DEFAULT_SERVER_ADDRESS)
    parser.add_argument('port', nargs='?', default=DEFAULT_SERVER_PORT, type=int)
    parser.add_argument('--name', '-n', nargs='?', type=str)
    args = parser.parse_args()
    return args


class GBChatClient(metaclass=ClientVerifier):
    port = PortDescriptor()

    def __init__(self, server_address, server_port, user_name):
        self.server_address = server_address
        self.server_port = server_port
        self.user_name = user_name
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(SOCKET_TIMEOUT)
        self.sock.connect((self.server_address, self.server_port))
        self.storage = ClientDBStorage(self.user_name)

    def __init_storage(self):
        try:
            with socket_lock:
                users_list = self.create_list_request_message('known', USERS_REQUEST, ACCOUNT_NAME)
        except ServerError as e:
            logger.error(e)
        else:
            self.storage.add_known_users(users_list)

        try:
            with socket_lock:
                users_list = self.create_list_request_message('contacts', GET_CONTACTS, USER)
        except ServerError as e:
            logger.error(e)
        else:
            for contact in users_list:
                self.storage.add_contact(contact)

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
        with db_lock:
            if not self.storage.known_user_exists(receiver):
                print(f'\nNo user {receiver} exists\n')
                return
        message = input('Please input message to send: ')
        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.user_name,
            DESTINATION: receiver,
            TIME: time.time(),
            MESSAGE_TEXT: message,
        }
        logger.debug(f'Message dict formed: {message_dict}')
        with db_lock:
            self.storage.save_message(self.user_name, receiver, message)
        with socket_lock:
            try:
                send_message(self.sock, message_dict)
            except OSError as e:
                if e.errno:
                    logger.critical(f'Could not send message from {self.user_name} to {receiver}. Error: {e}')
                    sys.exit(1)

    def create_list_request_message(self, list_name: str, request_action: str, request_parameter: str):
        logger.debug(f'Requesting {list_name} users of {self.user_name}')
        request = {
            ACTION: request_action,
            TIME: time.time(),
            request_parameter: self.user_name,
        }
        send_message(self.sock, request)
        answer = get_message(self.sock)
        if RESPONSE in answer and answer[RESPONSE] == 202:
            return answer[LIST_INFO]
        else:
            raise ServerError('Could not retrieve users list from server')

    def create_contact_action_message(self, contact: str, message: str, action: str):
        logger.debug(f'{message}ing contact {contact}')
        request = {
            ACTION: action,
            TIME: time.time(),
            USER: self.user_name,
            ACCOUNT_NAME: contact
        }
        with socket_lock:
            send_message(self.sock, request)
            answer = get_message(self.sock)
        if RESPONSE in answer and answer[RESPONSE] == 200:
            pass
        else:
            raise ServerError(f'Could not {message} contact: {contact}')
        print(f'Contact {contact} {message}d successfully')

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

        self.__init_storage()

        receiver = GBChatClientReceiverThread(self)
        sender = GBChatClientSenderThread(self)

        receiver.start()
        sender.start()

        logger.info(f'Client {self.user_name} had successfully started')

        while receiver.is_alive() and sender.is_alive():
            time.sleep(1)


class GBChatClientReceiverThread(Thread):
    def __init__(self, client: GBChatClient):
        super().__init__()
        self.daemon = True
        self.client = client

    def run(self) -> None:
        while True:
            time.sleep(1)
            with socket_lock:
                try:
                    message = get_message(self.client.sock)
                    if ACTION in message and message[ACTION] == MESSAGE and \
                            SENDER in message and DESTINATION in message and MESSAGE_TEXT in message and \
                            message[DESTINATION] == self.client.user_name:
                        print(f'\nReceived message from {message[SENDER]}: {message[MESSAGE_TEXT]}')
                    else:
                        logger.error(f'Incorrect message received: {message}')
                except OSError as e:
                    if e.errno:
                        logger.critical(f'{e} while receiving message. Quitting...')
                        sys.exit(1)


class GBChatClientSenderThread(Thread):
    def __init__(self, client: GBChatClient):
        super().__init__()
        self.daemon = True
        self.client = client

    def edit_contacts(self):
        answer = input('Input del to delete contact, or add for adding: ')
        if answer == 'del':
            contact = input('Input contact to delete: ')
            with db_lock:
                if self.client.storage.contact_exists(contact):
                    self.client.storage.delete_contact(contact)
                    try:
                        self.client.create_contact_action_message(contact, 'delete', REMOVE_CONTACT)
                    except ServerError:
                        logger.error('Could not delete contact on server.')
                else:
                    logger.error('No contact to delete.')
        elif answer == 'add':
            contact = input('Input contact to add: ')
            with db_lock:
                if self.client.storage.known_user_exists(contact):
                    self.client.storage.add_contact(contact)
                    try:
                        self.client.create_contact_action_message(contact, 'create', ADD_CONTACT)
                    except ServerError:
                        logger.error('Could not delete contact on server.')

    def print_history(self):
        command = input('Show incoming messages- in, outgoing - out, all - просто Enter: ')
        with db_lock:
            if command == 'in':
                history_list = self.client.storage.get_history(to_user=self.client.user_name)
                for message in history_list:
                    print(f'\nMessage from user: {message[0]} '
                          f'date {message[3]}:\n{message[2]}')
            elif command == 'out':
                history_list = self.client.storage.get_history(from_user=self.client.user_name)
                for message in history_list:
                    print(f'\nMessage to user: {message[1]} '
                          f'date {message[3]}:\n{message[2]}')
            else:
                history_list = self.client.storage.get_history()
                for message in history_list:
                    print(f'\nMessage from user: {message[0]},'
                          f' to user {message[1]} '
                          f'date {message[3]}\n{message[2]}')

    @staticmethod
    def __print_help():
        print('Available commands:')
        print('message')
        print('history')
        print('contacts')
        print('edit')
        print('help')
        print('exit')

    def run(self):
        self.__print_help()
        while True:
            command = input('Please input a command: ')
            if command == 'message':
                self.client.create_text_message()
            elif command == 'help':
                self.__print_help()
            elif command == 'exit':
                with socket_lock:
                    send_message(self.client.sock, self.client.create_exit_message())
                print('Closing client. Bye.')
                time.sleep(0.5)
                break
            elif command == 'contacts':
                with db_lock:
                    contacts_list = self.client.storage.get_contacts()
                print('Contacts:', ', '.join(contacts_list))
            elif command == 'edit':
                self.edit_contacts()
            elif command == 'history':
                self.print_history()
            else:
                print('Incorrect command')


def main():
    arguments = parse_arguments()
    if not arguments.name:
        arguments.name = input('Please input user name: ')
    client = GBChatClient(arguments.address, arguments.port, arguments.name)
    client.main_loop()


if __name__ == '__main__':
    main()
