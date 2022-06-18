import sys
import logging

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QLabel, QComboBox, QPushButton, QApplication

from client.client_storage import ClientDBStorage
from client.client_transport import GBChatClientTransport

sys.path.append('../')
logger = logging.getLogger('client_logger')


class ClientAddContactDialog(QDialog):
    def __init__(self, trans: GBChatClientTransport, storage: ClientDBStorage):
        super().__init__()
        self.transport = trans
        self.storage = storage

        self.setFixedSize(350, 120)
        self.setWindowTitle('Select contact to add:')
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)

        self.selector_label = QLabel('Select contact to add:', self)
        self.selector_label.setFixedSize(200, 20)
        self.selector_label.move(10, 0)

        self.selector = QComboBox(self)
        self.selector.setFixedSize(200, 20)
        self.selector.move(10, 30)

        self.btn_refresh = QPushButton('Renew list', self)
        self.btn_refresh.setFixedSize(100, 30)
        self.btn_refresh.move(60, 60)

        self.btn_ok = QPushButton('Add', self)
        self.btn_ok.setFixedSize(100, 30)
        self.btn_ok.move(230, 20)

        self.btn_cancel = QPushButton('Cancel', self)
        self.btn_cancel.setFixedSize(100, 30)
        self.btn_cancel.move(230, 60)
        self.btn_cancel.clicked.connect(self.close)

        self.possible_contacts_update()
        self.btn_refresh.clicked.connect(self.update_possible_contacts)

    def possible_contacts_update(self):
        self.selector.clear()
        contacts_list = set(self.storage.get_contacts())
        users_list = set(self.storage.get_known_users())
        users_list.remove(self.transport.user_name)
        self.selector.addItems(users_list - contacts_list)

    def update_possible_contacts(self):
        try:
            self.transport.known_users_list_update()
        except OSError:
            pass
        else:
            logger.debug('Successfully fetched users list from server')
            self.possible_contacts_update()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    db = ClientDBStorage('test')
    transport = GBChatClientTransport('127.0.0.1', 7777, db, 'test')
    window = ClientAddContactDialog(transport, db)
    window.show()
    app.exec_()
