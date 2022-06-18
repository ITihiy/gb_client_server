from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QLabel, QComboBox, QPushButton, QApplication


class DelUserDialog(QDialog):
    def __init__(self, storage, server_processor):
        super().__init__()
        self.storage = storage
        self.server = server_processor

        self.setFixedSize(350, 120)
        self.setWindowTitle('Delete user')
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)

        self.selector_label = QLabel('Select user to delete:', self)
        self.selector_label.setFixedSize(200, 20)
        self.selector_label.move(10, 0)

        self.selector = QComboBox(self)
        self.selector.setFixedSize(200, 20)
        self.selector.move(10, 30)

        self.btn_ok = QPushButton('Delete', self)
        self.btn_ok.setFixedSize(100, 30)
        self.btn_ok.move(230, 20)
        self.btn_ok.clicked.connect(self.remove_user)

        self.btn_cancel = QPushButton('Отмена', self)
        self.btn_cancel.setFixedSize(100, 30)
        self.btn_cancel.move(230, 60)
        self.btn_cancel.clicked.connect(self.close)

        self.all_users_fill()

    def all_users_fill(self):
        self.selector.addItems([item[0] for item in self.storage.all_users_list()])

    def remove_user(self):
        self.storage.unregister_user(self.selector.currentText())
        if self.selector.currentText() in self.server.names:
            sock = self.server.client_names[self.selector.currentText()]
            del self.server.client_names[self.selector.currentText()]
            self.server.remove_client(sock)
        self.server.service_update_lists()
        self.close()


if __name__ == '__main__':
    app = QApplication([])
    from server.server_storage import ServerDBStorage

    database = ServerDBStorage('../server_db.sqlite')
    import os
    import sys

    path1 = os.path.join(os.getcwd(), '..')
    sys.path.insert(0, path1)
    from server.server_core import ServerMessageProcessor

    server = ServerMessageProcessor('127.0.0.1', 7777, database)
    dial = DelUserDialog(database, server)
    dial.show()
    app.exec_()
