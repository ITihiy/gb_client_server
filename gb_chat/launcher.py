import os

from subprocess import Popen, CREATE_NEW_CONSOLE

NUM_CLIENTS = 3

FILES_PATH = os.path.dirname(os.path.abspath(__file__))

HEADER = 'Choose an action: q - quit, s - launch server, k - launch clients, x - close all windows'

processes = []

while True:
    command = input(HEADER)
    if command == 'q':
        break
    elif command == 's':
        processes.append(Popen('python server.py', creationflags=CREATE_NEW_CONSOLE))
    elif command == 'k':
        print('Make sure enough clients are registered with password 123456.')
        for i in range(NUM_CLIENTS):
            processes.append(Popen(f'python client.py -n test-{i} -p 123456', creationflags=CREATE_NEW_CONSOLE))

    elif command == 'x':
        while processes:
            current_process = processes.pop()
            current_process.kill()
