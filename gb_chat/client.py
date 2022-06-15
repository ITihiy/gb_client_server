import argparse
import logging
import os
import sys

from PyQt5.QtWidgets import QApplication

from client.client_storage import ClientDBStorage
from client.client_transport import GBChatClientTransport
from client.main_client_window import ClientMainWindow
from client.request_user_name_dialog import UserNameDialog
from errors import ServerError
from gbc_common.variables import *

sys.path.append(os.path.join(os.getcwd(), '..'))

logger = logging.getLogger('client_logger')


def parse_arguments():
    parser = argparse.ArgumentParser(description='GB CLI chat client')
    parser.add_argument('address', nargs='?', default=DEFAULT_SERVER_ADDRESS)
    parser.add_argument('port', nargs='?', default=DEFAULT_SERVER_PORT, type=int)
    parser.add_argument('--name', '-n', default=None, nargs='?', type=str)
    arguments = parser.parse_args()
    if arguments.port < 1024 or arguments.port > 65535:
        raise ValueError(f'Incorrect port number {arguments.port}. Should be in range (1024-65535)')
    return arguments


if __name__ == '__main__':
    args = parse_arguments()
    app = QApplication(sys.argv)
    client_name = args.name
    if not args.name:
        start_dialog = UserNameDialog()
        app.exec_()
        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name.text()
            del start_dialog
        else:
            exit(0)
    logger.info(f'Client {client_name} started. Server {args.address}:{args.port}')

    db = ClientDBStorage(client_name)
    transport = None
    try:
        transport = GBChatClientTransport(args.address, args.port, db, client_name)
    except ServerError as error:
        print(error.text)
        exit(1)
    transport.start()
    main_window = ClientMainWindow(transport, db)
    main_window.make_connection(transport)
    main_window.setWindowTitle(f'GB Chat alpha release - {client_name}')
    app.exec_()

    transport.shutdown()
    transport.join()
