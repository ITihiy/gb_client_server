import argparse
import logging
import os
import socket
import sys

import select


from gbc_common.util import get_message, send_message
from gbc_common.variables import *

sys.path.append(os.path.join(os.getcwd(), '..'))

logger = logging.getLogger('server_logger')


def parse_arguments():
    parser = argparse.ArgumentParser(description='GB CLI chat server')
    parser.add_argument('-p', dest='port', default=DEFAULT_SERVER_PORT, type=int)
    parser.add_argument('-a', dest='address', default=DEFAULT_SERVER_LISTEN_ADDRESS)
    args = parser.parse_args()
    if args.port < 1024 or args.port > 65355:
        logger.critical(f'server called with incorrect port number: {args.port}')
        raise ValueError('Invalid port number. Should be in range 1025-65535')
    return args



class GBChatServer:
    def __init__(self, listen_address, listen_port):
        self.address = listen_address
        self.port = listen_port
        self.clients_list = []
        self.messages_list = []
        self.clients_names = {}
        self.sock = None


    def init_server_socket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.address, self.port))
        self.sock.listen(MAX_CONNECTIONS)
        self.sock.settimeout(0.5)
        logger.info(f'server is listening at {self.address}:{self.port}')

    def send_message_to_client(self, message, clients_sockets):
        if message[DESTINATION] in self.clients_names and self.clients_names[message[DESTINATION]] in clients_sockets:
            send_message(self.clients_names[message[DESTINATION]], message)
        else:
            error_text = f'Cannot send message to {message[DESTINATION]}'
            logger.error(error_text)
            raise Exception(error_text)

    def process_client_message(self, message, client):
        logger.debug(f'Processing message from client: {message}')
        if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message:
            if message[USER][ACCOUNT_NAME] not in self.clients_names:
                self.clients_names[message[USER][ACCOUNT_NAME]] = client
                send_message(client, OK_RESPONSE)
            else:
                response = ERROR_RESPONSE
                response[ERROR] = f'Name {message[USER][ACCOUNT_NAME]} is already taken'
                send_message(client, response)
                self.clients_list.remove(client)
                client.close()
            return
        elif ACTION in message and message[ACTION] == MESSAGE and TIME in message and MESSAGE_TEXT in message and \
                SENDER in message and DESTINATION in message:
            self.messages_list.append(message)
            return
        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
            self.clients_list.remove(message[ACCOUNT_NAME])
            self.clients_names[message[ACCOUNT_NAME]].close()
            del self.clients_names[message[ACCOUNT_NAME]]
            return
        else:
            response = ERROR_RESPONSE
            response[ERROR] = f'Incorrect message: {message}'
            send_message(client, response)
            return

    def _process_recv_data_list(self, data_lst):
        for current_client in data_lst:
            try:
                self.process_client_message(get_message(current_client), current_client)
            except:
                logger.info(f'Client {current_client.getpeername()} disconnected')

    def main_loop(self):
        self.init_server_socket()
        while True:
            try:
                client_socket, address = self.sock.accept()
            except OSError as err:
                print(err.errno)
            else:
                logger.info(f'Connected with: {address}')
                self.clients_list.append(client_socket)

            recv_data_list = []
            send_data_list = []

            try:
                recv_data_list, send_data_list, _ = select.select(self.clients_list, self.clients_list, [], 0)
            except OSError:
                pass

            if len(recv_data_list) > 0:
                self._process_recv_data_list(recv_data_list)

            if len(self.messages_list) > 0 and len(send_data_list) > 0:
                for current_message in self.messages_list:
                    try:
                        self.send_message_to_client(current_message, send_data_list)
                    except Exception:
                        self.clients_list.remove(self.clients_names[current_message[DESTINATION]])
                        del self.clients_names[current_message[DESTINATION]]
                self.messages_list.clear()


def main():
    arguments = parse_arguments()
    server = GBChatServer(arguments.address, arguments.port)
    server.main_loop()


if __name__ == '__main__':
    main()
