import binascii
import hmac
import json
import logging
import os
import socket
import sys
import threading

import select

from gbc_common.decorators import login_required
from gbc_common.descrs import PortDescriptor
from gbc_common.util import send_message, get_message
from gbc_common.variables import *
from server.server_storage import ServerDBStorage

sys.path.append('../')
logger = logging.getLogger('server_logger')


class ServerMessageProcessor(threading.Thread):
    port = PortDescriptor()

    def __init__(self, address, port, storage: ServerDBStorage):
        super().__init__()
        self.address = address
        self.port = port
        self.storage = storage

        self.sock = None
        self.clients = []
        self.listen_sockets = None
        self.error_sockets = None

        self.running = True
        self.client_names = dict()

    def __init_socket(self):
        logger.info(f'Starting server at {self.address}:{self.port}')
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.address, self.port))
        self.sock.settimeout(0.5)
        self.sock.listen(MAX_CONNECTIONS)

    def auth_user(self, message: dict, sock: socket.socket):
        logger.debug(f'Starting authorization of user {message[USER]}')
        if message[USER][ACCOUNT_NAME] in self.client_names:
            response = ERROR_RESPONSE
            response[ERROR] = 'User name is already taken'
            try:
                send_message(sock, response)
            except OSError:
                pass
            self.clients.remove(sock)
            sock.close()
        elif not self.storage.check_user_exists(message[USER][ACCOUNT_NAME]):
            response = ERROR_RESPONSE
            response[ERROR] = 'User is not registered'
            try:
                send_message(sock, response)
            except OSError:
                pass
            self.clients.remove(sock)
            sock.close()
        else:
            logger.debug(f'User name {message[USER][ACCOUNT_NAME]} is correct. Starting password check')
            response = AUTH_RESPONSE
            random_string = binascii.hexlify(os.urandom(64))
            response[DATA] = random_string.decode('ascii')
            random_hash = hmac.new(self.storage.get_hash(message[USER][ACCOUNT_NAME]), random_string, 'MD5')
            digest = random_hash.digest()
            logger.debug(f'Auth message = {response}')
            try:
                send_message(sock, response)
                answer = get_message(sock)
            except OSError as err:
                logger.debug('Error in auth, data:', exc_info=err)
                sock.close()
                return
            client_digest = binascii.a2b_base64(answer[DATA])
            if RESPONSE in answer and answer[RESPONSE] == 511 and hmac.compare_digest(digest, client_digest):
                self.client_names[message[USER][ACCOUNT_NAME]] = sock
                client_ip, client_port = sock.getpeername()
                try:
                    send_message(sock, OK_RESPONSE)
                except OSError:
                    self.remove_client(message[USER][ACCOUNT_NAME])
                self.storage.login_user(message[USER][ACCOUNT_NAME], client_ip, client_port, message[USER][PUBLIC_KEY])
            else:
                response = ERROR_RESPONSE
                response[ERROR] = 'Incorrect password.'
                try:
                    send_message(sock, response)
                except OSError:
                    pass
                self.clients.remove(sock)
                sock.close()

    def remove_client(self, client):
        logger.info(f'Client {client.getpeername()} disconnected from server.')
        for name in self.client_names:
            if self.client_names[name] == client:
                self.storage.logout_user(name)
                del self.client_names[name]
                break
        self.clients.remove(client)
        client.close()

    def process_message(self, message):
        if message[DESTINATION] in self.client_names and self.client_names[message[DESTINATION]] in self.listen_sockets:
            try:
                send_message(self.client_names[message[DESTINATION]], message)
                logger.info(
                    f'Sent message to user {message[DESTINATION]} from user {message[SENDER]}.')
            except OSError:
                self.remove_client(message[DESTINATION])
        elif message[DESTINATION] in self.client_names \
                and self.client_names[message[DESTINATION]] not in self.listen_sockets:
            logger.error(
                f'Connection with {message[DESTINATION]} was lost. Unable to send message.')
            self.remove_client(self.client_names[message[DESTINATION]])
        else:
            logger.error(f'User {message[DESTINATION]} is not registered, unable to send message.')

    @login_required
    def process_client_message(self, message: dict, client: socket.socket):
        logger.debug(f'Processing message from client : {message}')
        if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message:
            self.auth_user(message, client)

        elif ACTION in message and message[ACTION] == MESSAGE and DESTINATION in message and TIME in message \
                and SENDER in message and MESSAGE_TEXT in message and self.client_names[message[SENDER]] == client:
            if message[DESTINATION] in self.client_names:
                self.storage.message_history_update(message[SENDER], message[DESTINATION])
                self.process_message(message)
                try:
                    send_message(client, OK_RESPONSE)
                except OSError:
                    self.remove_client(client)
            else:
                response = ERROR_RESPONSE
                response[ERROR] = 'User is not registered on server.'
                try:
                    send_message(client, response)
                except OSError:
                    pass
            return

        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message \
                and self.client_names[message[ACCOUNT_NAME]] == client:
            self.remove_client(client)

        elif ACTION in message and message[ACTION] == GET_CONTACTS and USER in message and \
                self.client_names[message[USER]] == client:
            response = ACCEPTED_RESPONSE
            response[LIST_INFO] = self.storage.get_all_contacts(message[USER])
            try:
                send_message(client, response)
            except OSError:
                self.remove_client(client)

        elif ACTION in message and message[ACTION] == ADD_CONTACT and ACCOUNT_NAME in message and USER in message \
                and self.client_names[message[USER]] == client:
            self.storage.add_contact(message[USER], message[ACCOUNT_NAME])
            try:
                send_message(client, OK_RESPONSE)
            except OSError:
                self.remove_client(client)

        elif ACTION in message and message[ACTION] == REMOVE_CONTACT and ACCOUNT_NAME in message and USER in message \
                and self.client_names[message[USER]] == client:
            self.storage.delete_contact(message[USER], message[ACCOUNT_NAME])
            try:
                send_message(client, OK_RESPONSE)
            except OSError:
                self.remove_client(client)

        elif ACTION in message and message[ACTION] == USERS_REQUEST and ACCOUNT_NAME in message \
                and self.client_names[message[ACCOUNT_NAME]] == client:
            response = ACCEPTED_RESPONSE
            response[LIST_INFO] = [user[0] for user in self.storage.all_users_list()]
            try:
                send_message(client, response)
            except OSError:
                self.remove_client(client)

        elif ACTION in message and message[ACTION] == PUBLIC_KEY_REQUEST and ACCOUNT_NAME in message:
            response = AUTH_RESPONSE
            response[DATA] = self.storage.get_public_key(message[ACCOUNT_NAME])
            if response[DATA]:
                try:
                    send_message(client, response)
                except OSError:
                    self.remove_client(client)
            else:
                response = ERROR_RESPONSE
                response[ERROR] = 'No public key exists for user'
                try:
                    send_message(client, response)
                except OSError:
                    self.remove_client(client)

        else:
            response = ERROR_RESPONSE
            response[ERROR] = 'Incorrect request.'
            try:
                send_message(client, response)
            except OSError:
                self.remove_client(client)

    def service_update_lists(self):
        for client in self.client_names:
            try:
                send_message(self.client_names[client], RESET_RESPONSE)
            except OSError:
                self.remove_client(self.client_names[client])

    def run(self) -> None:
        self.__init_socket()
        while self.running:
            try:
                client, client_address = self.sock.accept()
            except OSError:
                pass
            else:
                logger.info(f'Connected client from {client_address}')
                client.settimeout(5)
                self.clients.append(client)

            recv_data_lst = []
            try:
                if self.clients:
                    recv_data_lst, _, _ = select.select(self.clients, self.clients, [], 0)
            except OSError as err:
                logger.error(f'Error working with socket: {err.errno}')

            if recv_data_lst:
                for client_with_message in recv_data_lst:
                    try:
                        self.process_client_message(get_message(client_with_message), client_with_message)
                    except (OSError, json.JSONDecodeError, TypeError) as err:
                        logger.debug(f'Getting data from client exception.', exc_info=err)
                        self.remove_client(client_with_message)
