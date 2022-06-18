import argparse
import configparser
import logging
import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from gbc_common.variables import *
from logs.log_decorator import log
from server.main_window import MainWindow
from server.server_core import ServerMessageProcessor
from server.server_storage import ServerDBStorage

logger = logging.getLogger('server_logger')


@log
def arg_parser(default_port, default_address):
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=default_port, type=int, nargs='?')
    parser.add_argument('-a', default=default_address, nargs='?')
    parser.add_argument('--no_gui', action='store_true')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p
    gui_flag = namespace.no_gui
    logger.debug('Arguments loaded.')
    return listen_address, listen_port, gui_flag


@log
def config_load():
    config = configparser.ConfigParser()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")
    if 'SETTINGS' in config:
        return config
    else:
        config.add_section('SETTINGS')
        config.set('SETTINGS', 'default_port', str(DEFAULT_SERVER_PORT))
        config.set('SETTINGS', 'listen_Address', '')
        config.set('SETTINGS', 'database_path', '')
        config.set('SETTINGS', 'database_file', 'server_db.sqlite')
        return config


@log
def main():
    config = config_load()

    listen_address, listen_port, gui_flag = arg_parser(
        config['SETTINGS']['default_port'], config['SETTINGS']['listen_Address'])

    database = ServerDBStorage(os.path.join(config['SETTINGS']['Database_path'], config['SETTINGS']['Database_file']))

    server = ServerMessageProcessor(listen_address, listen_port, database)
    server.daemon = True
    server.start()

    if gui_flag:
        while True:
            command = input('Input exit to stop server.')
            if command == 'exit':
                server.running = False
                server.join()
                break
    else:
        server_app = QApplication(sys.argv)
        server_app.setAttribute(Qt.AA_DisableWindowContextHelpButton)
        main_window = MainWindow(database, server, config)
        server_app.exec_()
        server.running = False


if __name__ == '__main__':
    main()
