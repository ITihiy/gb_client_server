import socket
import time
import argparse
import sys
import os

sys.path.append(os.path.join(os.getcwd(), '..'))


from gb_chat.gbc_common.variables import *
from gb_chat.gbc_common.util import get_message, send_message


def parse_arguments():
    parser = argparse.ArgumentParser(description='GB CLI chat client')
    parser.add_argument('address', nargs='?', default=DEFAULT_SERVER_ADDRESS)
    parser.add_argument('port', nargs='?', default=DEFAULT_SERVER_PORT, type=int)
    args = parser.parse_args()
    if args.port < 1024 or args.port > 65355:
        raise ValueError('Invalid port number. Should be in range 1025-65535')
    return args


def create_presence_message(account_name='Guest'):
    return {
        ACTION: PRESENCE,
        TIME: time.time(),
        USER: {
            ACCOUNT_NAME: account_name,
        },
    }


def process_answer(message):
    if RESPONSE in message and message[RESPONSE] == 200:
        return '200: OK'
    elif RESPONSE in message:
        return f'400: {message[ERROR]}'
    raise ValueError


def main():
    args = parse_arguments()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((args.address, args.port))
    send_message(sock, create_presence_message())
    reply = process_answer(get_message(sock))
    print(reply)
    sock.close()


if __name__ == '__main__':
    main()
