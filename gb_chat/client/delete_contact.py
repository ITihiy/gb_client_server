import logging
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QLabel, QComboBox, QPushButton, QApplication

from client.client_storage import ClientDBStorage

sys.path.append('../')
logger = logging.getLogger('client_logger')


class ClientDeleteContactDialog(QDialog):
    def __init__(self, storage: ClientDBStorage):
        super().__init__()
        self.storage = storage

        self.setFixedSize(350, 120)
        self.setWindowTitle('Select contact to delete:')
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)

        self.selector_label = QLabel('Select contact to delete:', self)
        self.selector_label.setFixedSize(200, 20)
        self.selector_label.move(10, 0)

        self.selector = QComboBox(self)
        self.selector.setFixedSize(200, 20)
        self.selector.move(10, 30)
        self.selector.addItems(sorted(self.storage.get_contacts()))

        self.btn_ok = QPushButton('Delete', self)
        self.btn_ok.setFixedSize(100, 30)
        self.btn_ok.move(230, 20)

        self.btn_cancel = QPushButton('Cancel', self)
        self.btn_cancel.setFixedSize(100, 30)
        self.btn_cancel.move(230, 60)
        self.btn_cancel.clicked.connect(self.close)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    db = ClientDBStorage('test1')
    window = ClientDeleteContactDialog(db)
    db.add_contact('test1')
    db.add_contact('test2')
    print(db.get_contacts())
    window.selector.addItems(sorted(db.get_contacts()))
    window.show()
    app.exec_()
