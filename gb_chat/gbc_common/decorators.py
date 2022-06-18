import sys
import socket

from gbc_common.variables import PRESENCE, ACTION

sys.path.append('../')


def login_required(func):
    def inner(*args, **kwargs):
        from server.server_core import ServerMessageProcessor
        if isinstance(args[0], ServerMessageProcessor):
            found = False
            for arg in args:
                if isinstance(arg, socket.socket):
                    for client in args[0].names:
                        if args[0].names[client] == arg:
                            found = True

            for arg in args:
                if isinstance(arg, dict):
                    if ACTION in arg and arg[ACTION] == PRESENCE:
                        found = True
            if not found:
                raise TypeError
        return func(*args, **kwargs)

    return inner
