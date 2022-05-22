import os
import sys
import signal
import subprocess

from time import sleep

NUM_SEND_CLIENTS = 2
NUM_RECEIVE_CLIENTS = 2

PYTHON_PATH = sys.executable
FILES_PATH = os.path.dirname(os.path.abspath(__file__))

HEADER = 'Choose an action: q - quit, s - launch server and clients, x - close all windows'


def create_process(args):
    sleep(0.2)
    file_path = f'{PYTHON_PATH} {FILES_PATH}/{args}'
    return subprocess.Popen(['gnome-terminal', '--disable-factory', '--', 'bash', '-c', file_path],
                            preexec_fn=os.setpgrp())


processes = []

while True:
    command = input(HEADER)
    if command == 'q':
        break
    elif command == 's':
        if len(processes) > 0:
            print('Server and clients already running.')
        else:
            processes.append(create_process('server.py'))
            for _ in range(NUM_RECEIVE_CLIENTS):
                processes.append(create_process('client.py -m listen'))
            for _ in range(NUM_SEND_CLIENTS):
                processes.append(create_process('client.py -m send'))
    elif command == 'x':
        while processes:
            current_process = processes.pop()
            os.killpg(current_process.pid, signal.SIGINT)
