import argparse
import logging
import os
import socket
import sys
import configparser
from threading import Thread, Lock

import select
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMessageBox

from descrs import PortDescriptor
from gbc_common.util import get_message, send_message
from gbc_common.variables import *
from metaclasses import ServerVerifier
from server_gui import ServerGUIMainWindow, get_active_users_model, ServerGUIHistoryWindow, get_history_model, \
    ServerGUIConfigWindow, db_lock
from server_storage import ServerDBStorage

sys.path.append(os.path.join(os.getcwd(), '..'))

logger = logging.getLogger('server_logger')

new_connection = True
new_connection_lock = Lock()


def parse_arguments(default_port, default_address):
    parser = argparse.ArgumentParser(description='GB CLI chat server')
    parser.add_argument('-p', dest='port', default=default_port, type=int)
    parser.add_argument('-a', dest='address', default=default_address)
    args = parser.parse_args()
    return args.address, args.port


class GBChatServer(Thread, metaclass=ServerVerifier):
    port = PortDescriptor()

    def __init__(self, listen_address, listen_port, storage):
        super().__init__()
        self.daemon = True
        self.address = listen_address
        self.port = listen_port
        self.clients_list = []
        self.messages_list = []
        self.clients_names = {}
        self.storage = storage
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
            with db_lock:
                self.storage.message_history_update(message[SENDER], message[DESTINATION])
        else:
            error_text = f'Cannot send message to {message[DESTINATION]}'
            logger.error(error_text)
            raise Exception(error_text)

    def process_client_message(self, message: dict, client: socket):
        global new_connection
        logger.debug(f'Processing message from client: {message}')

        # Process PRESENCE message
        if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message:
            if message[USER][ACCOUNT_NAME] not in self.clients_names:
                self.clients_names[message[USER][ACCOUNT_NAME]] = client
                address, port = client.getpeername()
                with db_lock, new_connection_lock:
                    self.storage.login_user(message[USER][ACCOUNT_NAME], address, port)
                    new_connection = True
                send_message(client, OK_RESPONSE)
            else:
                response = ERROR_RESPONSE
                response[ERROR] = f'Name {message[USER][ACCOUNT_NAME]} is already taken'
                send_message(client, response)
                self.clients_list.remove(client)
                client.close()
            return

        # Process MESSAGE message
        elif ACTION in message and message[ACTION] == MESSAGE and TIME in message and MESSAGE_TEXT in message and \
                SENDER in message and DESTINATION in message:
            self.messages_list.append(message)
            return

        # Process EXIT message
        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
            self.clients_list.remove(self.clients_names[message[ACCOUNT_NAME]])
            with db_lock:
                self.storage.logout_user(message[ACCOUNT_NAME])
            self.clients_names[message[ACCOUNT_NAME]].close()
            del self.clients_names[message[ACCOUNT_NAME]]
            with new_connection_lock:
                new_connection = True
            return

        # Process GET_CONTACTS message
        elif ACTION in message and message[ACTION] == GET_CONTACTS and USER in message and \
                self.clients_names[message[USER]] == client:
            response = ACCEPTED_RESPONSE
            with db_lock:
                response[LIST_INFO] = self.storage.get_all_contacts(message[USER])
            send_message(client, response)
            return

        # Process ADD_CONTACT message
        elif ACTION in message and message[ACTION] == ADD_CONTACT and ACCOUNT_NAME in message and USER in message \
                and self.clients_names[message[USER]] == client:
            with db_lock:
                self.storage.add_contact(message[USER], message[ACCOUNT_NAME])
            send_message(client, OK_RESPONSE)
            return

        # Process REMOVE_CONTACT message
        elif ACTION in message and message[ACTION] == REMOVE_CONTACT and ACCOUNT_NAME in message and USER in message \
                and self.clients_names[message[USER]] == client:
            with db_lock:
                self.storage.delete_contact(message[USER], message[ACCOUNT_NAME])
            send_message(client, OK_RESPONSE)
            return

        # Process USERS_REQUEST message
        elif ACTION in message and message[ACTION] == USERS_REQUEST and ACCOUNT_NAME in message \
                and self.clients_names[message[ACCOUNT_NAME]] == client:
            response = ACCEPTED_RESPONSE
            with db_lock:
                response[LIST_INFO] = [user[0] for user in self.storage.all_users_list()]
            send_message(client, response)
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

    def run(self) -> None:
        self.init_server_socket()
        while True:
            try:
                client_socket, address = self.sock.accept()
            except OSError:
                pass
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


class GBChatServerStarter:
    server = None
    server_gui_app = None
    server_gui_window = None
    history_window = None
    server_configuration_window = None

    def __init__(self):
        self.config = configparser.ConfigParser()
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.config.read(f"{dir_path}/{'server.ini'}")
        self.listen_address, self.listen_port = parse_arguments(
            self.config['SETTINGS']['Default_port'], self.config['SETTINGS']['Listen_Address'])
        self.db = ServerDBStorage(
            os.path.join(self.config['SETTINGS']['Database_path'], self.config['SETTINGS']['Database_file']))

    def __get_active_users(self):
        global new_connection
        if new_connection:
            self.server_gui_window.active_clients_table.setModel(get_active_users_model(self.db))
            self.server_gui_window.active_clients_table.resizeColumnsToContents()
            self.server_gui_window.active_clients_table.resizeRowsToContents()
            with new_connection_lock:
                new_connection = False

    def __show_history_window(self):
        self.history_window = ServerGUIHistoryWindow()
        self.history_window.history_table.setModel(get_history_model(self.db))
        self.history_window.history_table.resizeColumnsToContents()
        self.history_window.history_table.resizeRowsToContents()
        self.history_window.show()

    def __show_server_config_window(self):
        self.server_configuration_window = ServerGUIConfigWindow()
        self.server_configuration_window.db_path.insert(self.config['SETTINGS']['database_path'])
        self.server_configuration_window.db_file.insert(self.config['SETTINGS']['database_file'])
        self.server_configuration_window.port.insert(self.config['SETTINGS']['default_port'])
        self.server_configuration_window.ip.insert(self.config['SETTINGS']['listen_address'])
        self.server_configuration_window.save_btn.clicked.connect(self.__save_server_config)

    def __save_server_config(self):
        message_window = QMessageBox()
        self.config['SETTINGS']['Database_path'] = self.server_configuration_window.db_path.text()
        self.config['SETTINGS']['Database_file'] = self.server_configuration_window.db_file.text()
        try:
            port = int(self.server_configuration_window.port.text())
        except ValueError:
            message_window.warning(self.server_configuration_window, 'Error', 'Port must be a number')
        else:
            self.config['SETTINGS']['Listen_Address'] = self.server_configuration_window.ip.text()
            if 1023 < port < 65536:
                self.config['SETTINGS']['Default_port'] = str(port)
                with open('server.ini', 'w') as conf:
                    self.config.write(conf)
                    message_window.information(self.server_configuration_window, 'OK', 'Settings saved')
            else:
                message_window.warning(
                    self.server_configuration_window, 'Error', 'Port must be in range 1024 to 65536')

    def start_gui_server(self):
        self.server = GBChatServer(self.listen_address, self.listen_port, self.db)
        self.server.start()
        self.server_gui_app = QApplication(sys.argv)
        self.server_gui_window = ServerGUIMainWindow()
        self.server_gui_window.statusBar().showMessage(f'Server is working at {self.listen_address}:{self.listen_port}')

        timer = QTimer()
        timer.timeout.connect(self.__get_active_users)
        timer.start(1000)

        self.server_gui_window.refresh_button.triggered.connect(self.__get_active_users)
        self.server_gui_window.history_button.triggered.connect(self.__show_history_window)
        self.server_gui_window.settings_button.triggered.connect(self.__show_server_config_window)

        self.server_gui_app.exec_()


# def main():
#     arguments = parse_arguments()
#     server = GBChatServer(arguments.address, arguments.port)
#     server.start()
#     while True:
#         print('Available commands: list: list all users, current: current active users, history: login history, exit')
#         current_command = input('Please input a command: ').strip()
#         if current_command == 'exit':
#             print('Quitting server. Bye.')
#             server.sock.close()
#             break
#         elif current_command == 'list':
#             for entry in server.storage.all_users_list():
#                 print(f'User: {entry[0]}, last login time: {entry[1]}')
#         elif current_command == 'current':
#             for entry in server.storage.current_users_list():
#                 print(f'User: {entry[0]}, last login time: {entry[3]} from {entry[1]}:{entry[2]}')
#         elif current_command == 'history':
#             user_name = input('Please enter user name (Enter for all): ').strip()
#             for entry in server.storage.history_list(user_name=user_name):
#                 print(f'User: {entry[0]}, last login time: {entry[1]} from {entry[2]}:{entry[3]}')


if __name__ == '__main__':
    starter = GBChatServerStarter()
    starter.start_gui_server()
