import argparse
import logging
import os
import socket
import sys

import select

from logs.log_decorator import log
from gbc_common.variables import *
from gbc_common.util import get_message, send_message

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
def process_client_message(message, messages_list, client, clients_list, clients_names):
    logger.debug(f'Processing message from client: {message}')
    if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message:
        if message[USER][ACCOUNT_NAME] not in clients_names:
            clients_names[message[USER][ACCOUNT_NAME]] = client
            send_message(client, OK_RESPONSE)
        else:
            response = ERROR_RESPONSE
            response[ERROR] = f'Name {message[USER][ACCOUNT_NAME]} is already taken'
            send_message(client, response)
            clients_list.remove(client)
            client.close()
        return
    elif ACTION in message and message[ACTION] == MESSAGE and TIME in message and MESSAGE_TEXT in message and \
            SENDER in message and DESTINATION in message:
        messages_list.append(message)
        return
    elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
        clients_list.remove(message[ACCOUNT_NAME])
        clients_names[message[ACCOUNT_NAME]].close()
        del clients_names[message[ACCOUNT_NAME]]
        return
    else:
        response = ERROR_RESPONSE
        response[ERROR] = f'Incorrect message: {message}'
        send_message(client, response)
        return


@log
def send_message_to_client(message, clients_names, clients_sockets):
    if message[DESTINATION] in clients_names and clients_names[message[DESTINATION]] in clients_sockets:
        send_message(clients_names[message[DESTINATION]], message)
    else:
        error_text = f'Cannot send message to {message[DESTINATION]}'
        logger.error(error_text)
        raise Exception(error_text)


def process_recv_data_list(data_lst, messages_lst, clients_lst, clients_names):
    for current_client in data_lst:
        try:
            process_client_message(get_message(current_client), messages_lst, current_client, clients_lst,
                                   clients_names)
        except:
            logger.info(f'Client {current_client.getpeername()} disconnected')


def main():
    with setup_server_socket() as sock:
        clients_list = []
        messages_list = []

        clients_names = {}

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

            try:
                recv_data_list, send_data_list, _ = select.select(clients_list, clients_list, [], 0)
            except OSError:
                pass

            if len(recv_data_list) > 0:
                process_recv_data_list(recv_data_list, messages_list, clients_list, clients_names)

            if len(messages_list) > 0 and len(send_data_list) > 0:
                for current_message in messages_list:
                    try:
                        send_message_to_client(current_message, clients_names, send_data_list)
                    except Exception:
                        clients_list.remove(clients_names[current_message[DESTINATION]])
                        del clients_names[current_message[DESTINATION]]
                messages_list.clear()


if __name__ == '__main__':
    main()
