import argparse
import socket
import sys
import os
import logging
import logs.server_log_config

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
    logger.info(f'server is listening at {args.address}:{args.port}')
    return server_socket


def process_client_message(message):
    if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message and message[USER][
        ACCOUNT_NAME] == 'Guest':
        logger.info(f'received presence message from {message[USER][ACCOUNT_NAME]}')
        return {RESPONSE: 200}
    logger.error('incorrect message received')
    return {
        RESPONSE: 400,
        ERROR: 'Bad request',
    }


def main():
    with setup_server_socket() as sock:
        while True:
            client_socket, address = sock.accept()
            message = get_message(client_socket)
            response = process_client_message(message)
            send_message(client_socket, response)
            client_socket.close()


if __name__ == '__main__':
    main()
