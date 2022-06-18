DEFAULT_SERVER_PORT = 7777
DEFAULT_SERVER_LISTEN_ADDRESS = ''
DEFAULT_SERVER_ADDRESS = '127.0.0.1'

MAX_CONNECTIONS = 10
BUFFER_SIZE = 4096

ENCODING = 'utf-8'

ACTION = 'action'
TIME = 'time'
USER = 'user'
ACCOUNT_NAME = 'account_name'
SENDER = 'sender'
DESTINATION = 'to'
DATA = 'bin'
PUBLIC_KEY = 'pubkey'

PRESENCE = 'presence'
RESPONSE = 'response'
ERROR = 'error'
EXIT = 'exit'
GET_CONTACTS = 'get_contacts'
LIST_INFO = 'data_list'
REMOVE_CONTACT = 'remove'
ADD_CONTACT = 'add'
USERS_REQUEST = 'get_users'
PUBLIC_KEY_REQUEST = 'pubkey_need'

MESSAGE = 'message'
MESSAGE_TEXT = 'mess_text'

OK_RESPONSE = {RESPONSE: 200}
ACCEPTED_RESPONSE = {RESPONSE: 202, LIST_INFO: None}
RESET_RESPONSE = {RESPONSE: 205}
ERROR_RESPONSE = {
    RESPONSE: 400,
    ERROR: None
}
AUTH_RESPONSE = {RESPONSE: 511, DATA: None}