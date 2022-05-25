import socket
import time
import argparse
import sys
import os
import logging
import logs.client_log_config

from logs.log_decorator import log

sys.path.append(os.path.join(os.getcwd(), '..'))

from gbc_common.variables import *
from gbc_common.util import get_message, send_message

logger = logging.getLogger('client_logger')


def parse_arguments():
    parser = argparse.ArgumentParser(description='GB CLI chat client')
    parser.add_argument('address', nargs='?', default=DEFAULT_SERVER_ADDRESS)
    parser.add_argument('port', nargs='?', default=DEFAULT_SERVER_PORT, type=int)
    parser.add_argument('--mode', '-m', default='listen', nargs='?', type=str)
    args = parser.parse_args()
    if args.port < 1024 or args.port > 65355:
        logger.critical(f'client called with incorrect port number: {args.port}')
        raise ValueError('Invalid port number. Should be in range 1025-65535')
    if args.mode not in ['send', 'listen']:
        logger.critical(f'client called in incorrect mode: {args.mode}. ("send" or "listen" allowed)')
        raise ValueError('Invalid client mode. ("send" or "listen" allowed)')
    return args


@log
def create_presence_message(account_name='Guest'):
    logger.info(f'presence message with account {account_name} created')
    return {
        ACTION: PRESENCE,
        TIME: time.time(),
        USER: {
            ACCOUNT_NAME: account_name,
        },
    }


@log
def create_text_message(server_socket, account_name='Guest'):
    message = input('Please input message to send or \'!!!\' to quit: ')
    if message == '!!!':
        server_socket.close()
        logger.info('Quitting client.')
        sys.exit(0)
    else:
        result_message = {
            ACTION: MESSAGE,
            ACCOUNT_NAME: account_name,
            TIME: time.time(),
            MESSAGE_TEXT: message,
        }
        logger.info(f'Message "{message}" was formed')
        return result_message


def process_text_message(message):
    if ACTION in message and message[ACTION] == MESSAGE and SENDER in message and MESSAGE_TEXT in message:
        answer = f'Received message from user {message[SENDER]}:\n{message[MESSAGE_TEXT]}'
        print(answer)
        logger.info(answer)
    else:
        logger.error(f'Received incorrect message: {message}')


@log
def process_response_answer(message):
    if RESPONSE in message and message[RESPONSE] == 200:
        return '200: OK'
    elif RESPONSE in message and message[RESPONSE] == 400:
        raise ValueError(f'400: {message[ERROR]}')
    raise ValueError


def create_client_socket(args):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((args.address, args.port))
    return sock


def main():
    args = parse_arguments()
    with create_client_socket(args) as sock:
        logger.info(f'Client started with parameters: {args.address}:{args.port} in {args.mode} mode.')
        try:
            send_message(sock, create_presence_message())
            answer = process_response_answer(get_message(sock))
            logger.info(f'Successfully connected to server: {args.address}:{args.port}. Answer was: {answer}')
        except ValueError as err:
            logger.critical(f'Failed connecting to server: {err}')
            sys.exit(1)
        print('Client mode - listen' if args.mode == 'listen' else 'Client mode - send')

        while True:
            if args.mode == 'listen':
                try:
                    process_text_message(get_message(sock))
                except:
                    logger.debug('Server disconnected')
                    sys.exit(1)
            if args.mode == 'send':
                send_message(sock, create_text_message(sock))


if __name__ == '__main__':
    main()
