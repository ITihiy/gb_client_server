import json

from .variables import BUFFER_SIZE, ENCODING


def get_message(client_socket):
    raw_response = client_socket.recv(BUFFER_SIZE)
    if not isinstance(raw_response, bytes):
        raise ValueError
    str_response = raw_response.decode(ENCODING)
    if not isinstance(str_response, str):
        raise ValueError
    json_result = json.loads(str_response)
    if not isinstance(json_result, dict):
        raise ValueError
    return json_result


def send_message(sock, message):
    if not isinstance(message, dict):
        raise TypeError
    json_message = json.dumps(message)
    sock.send(json_message.encode(ENCODING))
