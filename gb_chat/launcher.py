import os

from subprocess import Popen, CREATE_NEW_CONSOLE

NUM_CLIENTS = 3

FILES_PATH = os.path.dirname(os.path.abspath(__file__))

HEADER = 'Choose an action: q - quit, s - launch server and clients, x - close all windows'

processes = []

while True:
    command = input(HEADER)
    if command == 'q':
        break
    elif command == 's':
        if len(processes) > 0:
            print('Server and clients already running.')
        else:
            processes.append(Popen('python server.py', creationflags=CREATE_NEW_CONSOLE))
            for i in range(NUM_CLIENTS):
                processes.append(Popen(f'python client.py -n test-{i}', creationflags=CREATE_NEW_CONSOLE))

    elif command == 'x':
        while processes:
            current_process = processes.pop()
            current_process.kill()
