import argparse
import logging
import os
import socket
import sys
import time
from threading import Thread

from gbc_common.util import get_message, send_message
from gbc_common.variables import *
from logs.log_decorator import log

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


@log
def create_presence_message(account_name):
    logger.info(f'presence message with account {account_name} created')
    return {
        ACTION: PRESENCE,
        TIME: time.time(),
        USER: {
            ACCOUNT_NAME: account_name,
        },
    }


@log
def create_exit_message(account_name):
    logger.info(f'exit message with account {account_name} created')
    return {
        ACTION: EXIT,
        TIME: time.time(),
        ACCOUNT_NAME: account_name,
    }


@log
def create_text_message(server_socket, account_name):
    receiver = input('Please input user name to send message: ')
    message = input('Please input message to send: ')
    message_dict = {
        ACTION: MESSAGE,
        SENDER: account_name,
        DESTINATION: receiver,
        TIME: time.time(),
        MESSAGE_TEXT: message,
    }
    logger.debug(f'Message dict formed: {message_dict}')
    try:
        send_message(server_socket, message_dict)
    except Exception as e:
        logger.critical(f'Couldn\'t send message from {account_name} to {receiver}. Error: {e}')
        sys.exit(1)


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


@log
def receiver_main_loop(server_socket, user_name):
    while True:
        try:
            message = get_message(server_socket)
            if ACTION in message and message[ACTION] == MESSAGE and \
                    SENDER in message and DESTINATION in message and MESSAGE_TEXT in message and \
                    message[DESTINATION] == user_name:
                print(f'Received message from {message[SENDER]}: {message[MESSAGE_TEXT]}')
            else:
                logger.error(f'Incorrect message received: {message}')
        except Exception as e:
            logger.critical(f'{e} while receiving message. Quitting')
            sys.exit(1)


@log
def sender_main_loop(server_socket, user_name):
    print('Available commands: message, help, exit')
    while True:
        command = input('Please input a command: ')
        if command == 'message':
            create_text_message(server_socket, user_name)
        elif command == 'help':
            print('Available commands: message, help, exit')
        elif command == 'exit':
            send_message(server_socket, create_exit_message(user_name))
            print('Closing client. Bye.')
            time.sleep(0.5)
            break
        else:
            print('Incorrect command')


def main():
    args = parse_arguments()
    with create_client_socket(args) as sock:
        logger.info(f'Client started with parameters: {args.address}:{args.port} with {args.name} user name.')
        try:
            send_message(sock, create_presence_message(args.name))
            answer = process_response_answer(get_message(sock))
            logger.info(f'Successfully connected to server: {args.address}:{args.port}. Answer was: {answer}')
        except ValueError as err:
            logger.critical(f'Failed connecting to server: {err}')
            sys.exit(1)
        print(f'{args.name} successfully logged in to server {args.address}:{args.port}')

        receiver = Thread(target=receiver_main_loop, args=(sock, args.name), daemon=True)
        sender = Thread(target=sender_main_loop, args=(sock, args.name), daemon=True)

        receiver.start()
        sender.start()

        logger.info(f'Client {args.name} had successfully started')

        while receiver.is_alive() and sender.is_alive():
            time.sleep(1)


if __name__ == '__main__':
    main()
