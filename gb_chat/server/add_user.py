from PyQt5.QtWidgets import QDialog, QPushButton, QLineEdit, QApplication, QLabel, QMessageBox
from PyQt5.QtCore import Qt
import hashlib
import binascii

from server.server_storage import ServerDBStorage


class RegisterUser(QDialog):
    def __init__(self, storage: ServerDBStorage, server_processor):
        super().__init__()

        self.storage = storage
        self.server = server_processor

        self.setWindowTitle('Registration')
        self.setFixedSize(175, 183)
        self.setModal(True)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.label_username = QLabel('User name:', self)
        self.label_username.move(10, 10)
        self.label_username.setFixedSize(150, 15)

        self.client_name = QLineEdit(self)
        self.client_name.setFixedSize(154, 20)
        self.client_name.move(10, 30)

        self.label_passwd = QLabel('Password:', self)
        self.label_passwd.move(10, 55)
        self.label_passwd.setFixedSize(150, 15)

        self.client_passwd = QLineEdit(self)
        self.client_passwd.setFixedSize(154, 20)
        self.client_passwd.move(10, 75)
        self.client_passwd.setEchoMode(QLineEdit.Password)
        self.label_conf = QLabel('Confirm:', self)
        self.label_conf.move(10, 100)
        self.label_conf.setFixedSize(150, 15)

        self.client_conf = QLineEdit(self)
        self.client_conf.setFixedSize(154, 20)
        self.client_conf.move(10, 120)
        self.client_conf.setEchoMode(QLineEdit.Password)

        self.btn_ok = QPushButton('Save', self)
        self.btn_ok.move(10, 150)
        self.btn_ok.clicked.connect(self.save_data)

        self.btn_cancel = QPushButton('Exit', self)
        self.btn_cancel.move(90, 150)
        self.btn_cancel.clicked.connect(self.close)

        self.messages = QMessageBox()

        self.show()

    def save_data(self):
        if not self.client_name.text():
            self.messages.critical(self, 'Error', 'User name not set.')
            return
        elif self.client_passwd.text() != self.client_conf.text():
            self.messages.critical(self, 'Error', 'Passwords not matching.')
            return
        elif self.storage.check_user_exists(self.client_name.text()):
            self.messages.critical(self, 'Error', 'User already exists.')
            return
        else:
            password_bytes = self.client_passwd.text().encode('utf-8')
            salt = self.client_name.text().lower().encode('utf-8')
            password_hash = hashlib.pbkdf2_hmac('sha512', password_bytes, salt, 10000)
            self.storage.register_user(self.client_name.text(), binascii.hexlify(password_hash))
            self.messages.information(self, 'Success', 'User registered.')
            self.server.service_update_lists()
            self.close()


if __name__ == '__main__':
    app = QApplication([])
    db = ServerDBStorage('../server_db.sqlite')
    import os
    import sys
    from server.server_core import ServerMessageProcessor
    path1 = os.path.join(os.getcwd(), '..')
    sys.path.insert(0, path1)
    server = ServerMessageProcessor('127.0.0.1', 7777, db)
    dial = RegisterUser(db, server)
    app.exec_()
