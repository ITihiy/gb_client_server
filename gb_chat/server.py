import argparse
import select
import socket
import sys
import os
import logging
import time
import logs.server_log_config

from logs.log_decorator import log

sys.path.append(os.path.join(os.getcwd(), '..'))

from gbc_common.variables import *
from gbc_common.util import get_message, send_message

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


def setup_server_socket() -> socket:
    args = parse_arguments()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((args.address, args.port))
    server_socket.listen(MAX_CONNECTIONS)
    server_socket.settimeout(0.5)
    logger.info(f'server is listening at {args.address}:{args.port}')
    return server_socket


@log
def process_client_message(message, messages_list, client):
    logger.debug(f'Processing message from client: {message}')
    if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message and \
            message[USER][ACCOUNT_NAME] == 'Guest':
        send_message(client, {RESPONSE: 200})
        return
    elif ACTION in message and message[ACTION] == MESSAGE and TIME in message and MESSAGE_TEXT in message:
        messages_list.append((message[ACCOUNT_NAME], message[MESSAGE_TEXT]))
        return
    send_message(client, {RESPONSE: 400, ERROR: 'Bad request'})


def process_recv_data_list(data_lst, messages_lst, clients_lst):
    for current_client in data_lst:
        try:
            process_client_message(get_message(current_client), messages_lst, current_client)
        except:
            logger.info(f'Client {current_client.getpeername()} disconnected')
            clients_lst.remove(current_client)


def process_send_data_list(data_lst, messages_lst, clients_lst):
    current_message = {
        ACTION: MESSAGE,
        SENDER: messages_lst[0][0],
        TIME: time.time(),
        MESSAGE_TEXT: messages_lst[0][1],
    }
    del messages_lst[0]
    for current_client in data_lst:
        try:
            send_message(current_client, current_message)
        except:
            logger.info(f'Client {current_client.getpeername()} disconnected')
            current_client.close()
            clients_lst.remove(current_client)


def main():
    with setup_server_socket() as sock:
        clients_list = []
        messages_list = []

        while True:
            try:
                client_socket, address = sock.accept()
            except OSError as err:
                print(err.errno)
            else:
                logger.info(f'Connected with: {address}')
                clients_list.append(client_socket)
            recv_data_list = []
            send_data_list = []
            err_data_list = []

            try:
                recv_data_list, send_data_list, err_data_list = select.select(clients_list, clients_list, [], 0)
            except OSError:
                pass

            if len(recv_data_list) > 0:
                process_recv_data_list(recv_data_list, messages_list, clients_list)

            if len(messages_list) > 0 and len(send_data_list) > 0:
                process_send_data_list(send_data_list, messages_list, clients_list)


if __name__ == '__main__':
    main()
