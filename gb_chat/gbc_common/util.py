import json

from .variables import BUFFER_SIZE, ENCODING


def get_message(client_socket):
    raw_response = client_socket.recv(BUFFER_SIZE)
    if not isinstance(raw_response, bytes):
        raise ValueError
    str_response = raw_response.decode(ENCODING)
    json_result = json.loads(str_response)
    return json_result


def send_message(sock, message):
    if not isinstance(message, dict):
        raise TypeError
    json_message = json.dumps(message)
    sock.send(json_message.encode(ENCODING))
