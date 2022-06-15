import json
import logging
import socket
import sys
import threading
import time

from PyQt5.QtCore import QObject, pyqtSignal

from client.client_storage import ClientDBStorage
from errors import ServerError
from gbc_common.util import send_message, get_message
from gbc_common.variables import *

SOCKET_TIMEOUT = 5
CONNECTION_ATTEMPTS = 5
LOST_CONNECTION_ERROR = 'Lost connection with server'
TIMEOUT_ERROR = 'Connection timeout'

sys.path.append('..')
logger = logging.getLogger('client_logger')
socket_lock = threading.Lock()


class GBChatClientTransport(threading.Thread, QObject):
    new_message = pyqtSignal(str)
    connection_lost = pyqtSignal()

    def __init__(self, address, port, storage: ClientDBStorage, user_name):
        threading.Thread.__init__(self)
        QObject.__init__(self)
        self.user_name = user_name
        self.storage = storage
        self.sock = None
        self.__init_connection(address, port)
        try:
            self.known_users_list_update()
            self.contacts_list_update()
        except OSError as e:
            if e.errno:
                logger.critical(LOST_CONNECTION_ERROR)
                raise ServerError(LOST_CONNECTION_ERROR)
            logger.error('Timeout updating users lists')
        except json.JSONDecodeError:
            logger.critical(LOST_CONNECTION_ERROR)
            raise ServerError(LOST_CONNECTION_ERROR)
        self.running = True

    def __init_connection(self, address, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(SOCKET_TIMEOUT)
        is_connected = False
        for i in range(CONNECTION_ATTEMPTS):
            logger.info(f'Connection attempt #{i + 1}')
            try:
                self.sock.connect((address, port))
            except (OSError, ConnectionRefusedError):
                pass
            else:
                is_connected = True
                break
            time.sleep(1)
        if not is_connected:
            error_message = f'Could not connect to server {address}:{port}'
            logger.critical(error_message)
            raise ServerError(error_message)
        logger.debug(f'Connected to server {address}:{port}')
        try:
            with socket_lock:
                send_message(self.sock, self.create_presence_message())
                self.process_server_answer(get_message(self.sock))
        except (OSError, json.JSONDecodeError) as e:
            logger.critical('Lost connection with server')
            raise ServerError(e)
        logger.info(f'{self.user_name} connected to server {address}:{port} successfully')

    def create_presence_message(self):
        logger.info(f'presence message with account {self.user_name} created')
        return {
            ACTION: PRESENCE,
            TIME: time.time(),
            USER: {
                ACCOUNT_NAME: self.user_name,
            },
        }

    def process_server_answer(self, message):
        logger.debug(f'Processing message from server: {message}')
        if RESPONSE in message:
            if message[RESPONSE] == 400:
                raise ServerError(f'{message[ERROR]}')
            elif message[RESPONSE] in (200, 202):
                return
            else:
                logger.debug(f'Unknown response code: {message[RESPONSE]}')
        elif ACTION in message and message[ACTION] == MESSAGE and DESTINATION in message and MESSAGE_TEXT in message \
                and message[DESTINATION] == self.user_name:
            logger.debug(f'Received message from {message[SENDER]}: {message[MESSAGE_TEXT]}')
            self.storage.save_message(message[SENDER], 'in', message[MESSAGE_TEXT])
            self.new_message.emit(message[SENDER])
        else:
            print(f'Incorrect message: {message}')

    def known_users_list_update(self):
        logger.debug(f'Requesting known users for {self.user_name}')
        with socket_lock:
            send_message(self.sock, {ACTION: USERS_REQUEST, TIME: time.time(), ACCOUNT_NAME: self.user_name})
            answer = get_message(self.sock)
        if RESPONSE in answer and answer[RESPONSE] == 202:
            self.storage.add_known_users(answer[LIST_INFO])
        else:
            logger.error('Could not update known users list')

    def contacts_list_update(self):
        logger.debug(f'Requesting contacts for {self.user_name}')
        with socket_lock:
            send_message(self.sock, {ACTION: GET_CONTACTS, TIME: time.time(), USER: self.user_name})
            answer = get_message(self.sock)
        if RESPONSE in answer and answer[RESPONSE] == 202:
            for contact in answer[LIST_INFO]:
                self.storage.add_contact(contact)
        else:
            logger.error(f'Could not update contacts for {self.user_name}')

    def create_contact_action(self, contact: str, action: str):
        logger.debug(f'{action} contact {contact}')
        with socket_lock:
            send_message(self.sock, {ACTION: action, TIME: time.time(), USER: self.user_name, ACCOUNT_NAME: contact})
            self.process_server_answer(get_message(self.sock))

    def send_message(self, receiver: str, message: str):
        request = {
            ACTION: MESSAGE,
            SENDER: self.user_name,
            DESTINATION: receiver,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        with socket_lock:
            send_message(self.sock, request)
            self.process_server_answer(get_message(self.sock))
            logger.debug(f'Sent message to {receiver}. Message: {request}')

    def shutdown(self):
        self.running = False
        with socket_lock:
            try:
                send_message(self.sock, {ACTION: EXIT, TIME: time.time(), ACCOUNT_NAME: self.user_name})
            except OSError:
                pass
        logger.debug(f'Stopping transport for {self.user_name}')
        time.sleep(0.5)

    def run(self) -> None:
        logger.debug(f'Running transport thread for {self.user_name}')
        while self.running:
            time.sleep(1)
            with socket_lock:
                try:
                    self.sock.settimeout(0.5)
                    message = get_message(self.sock)
                except OSError as e:
                    if e.errno:
                        logger.critical(LOST_CONNECTION_ERROR)
                        self.running = False
                        self.connection_lost.emit()
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError, TypeError, json.JSONDecodeError):
                    logger.debug(LOST_CONNECTION_ERROR)
                    self.running = False
                    self.connection_lost.emit()
                else:
                    logger.debug(f'Received message from server: {message}')
                    self.process_server_answer(message)
                finally:
                    self.sock.settimeout(SOCKET_TIMEOUT)
