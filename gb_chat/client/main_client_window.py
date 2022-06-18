import logging
import sys

from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor
from PyQt5.QtWidgets import QMainWindow, qApp, QMessageBox, QApplication

from client.add_contact import ClientAddContactDialog
from client.client_storage import ClientDBStorage
from client.client_transport import GBChatClientTransport, LOST_CONNECTION_ERROR, TIMEOUT_ERROR
from client.delete_contact import ClientDeleteContactDialog
from client.main_client_window_raw import Ui_MainClientWindow
from gbc_common.errors import ServerError
from gbc_common.variables import *

MAX_MESSAGES = 20

sys.path.append('../')
logger = logging.getLogger('client_logger')


class ClientMainWindow(QMainWindow):
    def __init__(self, trans: GBChatClientTransport, storage: ClientDBStorage):
        super().__init__()
        self.transport = trans
        self.storage = storage
        self.current_chat = None
        self.contacts_model = None
        self.history_model = None
        self.messages = QMessageBox()

        self.ui = Ui_MainClientWindow()
        self.ui.setupUi(self)

        self.ui.list_messages.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.ui.list_messages.setWordWrap(True)

        self.ui.list_contacts.doubleClicked.connect(self.select_active_user)

        self.ui.menu_exit.triggered.connect(qApp.exit)
        self.ui.btn_send.clicked.connect(self.send_message)

        self.ui.btn_add_contact.clicked.connect(self.add_contact_window)
        self.ui.menu_add_contact.triggered.connect(self.add_contact_window)

        self.clients_list_update()
        self.set_disabled_input()
        self.show()

    def select_active_user(self):
        self.current_chat = self.ui.list_contacts.currentIndex().data()
        self.set_active_user()

    def set_active_user(self):
        self.ui.label_new_message.setText(f'Enter message for {self.current_chat}:')
        self.ui.btn_clear.setDisabled(False)
        self.ui.btn_send.setDisabled(False)
        self.ui.text_message.setDisabled(False)
        self.history_list_update()

    def send_message(self):
        text = self.ui.text_message.toPlainText()
        self.ui.text_message.clear()
        if not text:
            return
        try:
            self.transport.send_message(self.current_chat, text)
        except ServerError as e:
            self.messages.critical(self, 'Error', e.text)
        except OSError as e:
            if e.errno:
                self.messages.critical(self, 'Error', LOST_CONNECTION_ERROR)
                self.close()
            # self.messages.critical(self, 'Error', TIMEOUT_ERROR + ' main timeout')
        except (ConnectionResetError, ConnectionAbortedError):
            self.messages.critical(self, 'Error', LOST_CONNECTION_ERROR)
            self.close()
        finally:
            self.storage.save_message(self.current_chat, 'out', text)
            logger.debug(f'Sent message for {self.current_chat}: {text}')
            self.history_list_update()

    def history_list_update(self):
        messages_list = sorted(self.storage.get_history(self.current_chat), key=lambda x: x[3])
        if not self.history_model:
            self.history_model = QStandardItemModel()
        self.history_model.clear()
        self.ui.list_messages.setModel(self.history_model)
        start_idx = 0 if len(messages_list) <= MAX_MESSAGES else len(messages_list) - MAX_MESSAGES
        for idx in range(start_idx, len(messages_list)):
            current = messages_list[idx]
            if current[1] == 'in':
                message = QStandardItem(f'Incoming {current[3].replace(microsecond=0)}:\n {current[2]}')
                message.setBackground(QBrush(QColor(255, 213, 213)))
                message.setTextAlignment(Qt.AlignLeft)
                message.setEditable(False)
                self.history_model.appendRow(message)
            else:
                message = QStandardItem(f'Outgoing {current[3].replace(microsecond=0)}:\n {current[2]}')
                message.setTextAlignment(Qt.AlignRight)
                message.setBackground(QBrush(QColor(204, 255, 204)))
                message.setEditable(False)
                self.history_model.appendRow(message)
        self.ui.list_messages.scrollToBottom()

    def set_disabled_input(self):
        self.ui.label_new_message.setText('Double click contact to select')
        self.ui.text_message.clear()
        if self.history_model:
            self.history_model.clear()
        self.ui.btn_clear.setDisabled(True)
        self.ui.btn_send.setDisabled(True)
        self.ui.text_message.setDisabled(True)

    def clients_list_update(self):
        contacts_list = self.storage.get_contacts()
        self.contacts_model = QStandardItemModel()
        for i in sorted(contacts_list):
            item = QStandardItem(i)
            item.setEditable(False)
            self.contacts_model.appendRow(item)
        self.ui.list_contacts.setModel(self.contacts_model)

    def add_contact_action(self, item):
        new_contact = item.selector.currentText()
        self.add_contact(new_contact)
        item.close()

    def add_contact(self, new_contact):
        try:
            self.transport.create_contact_action(new_contact, ADD_CONTACT)
        except ServerError as err:
            self.messages.critical(self, 'Server error', err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Error', LOST_CONNECTION_ERROR)
                self.close()
            self.messages.critical(self, 'Error', TIMEOUT_ERROR)
        else:
            self.storage.add_contact(new_contact)
            new_contact = QStandardItem(new_contact)
            new_contact.setEditable(False)
            self.contacts_model.appendRow(new_contact)
            logger.info(f'Contact successfully added:  {new_contact}')
            self.messages.information(self, 'Success', 'Contact added')

    def add_contact_window(self):
        select_dialog = ClientAddContactDialog(self.transport, self.storage)
        select_dialog.btn_ok.clicked.connect(lambda: self.add_contact_action(select_dialog))
        select_dialog.show()

    def delete_contact_window(self):
        remove_dialog = ClientDeleteContactDialog(self.storage)
        remove_dialog.btn_ok.clicked.connect(lambda: self.delete_contact(remove_dialog))
        remove_dialog.show()

    def delete_contact(self, item):
        selected = item.selector.currentText()
        try:
            self.transport.create_contact_action(item, REMOVE_CONTACT)
        except ServerError as err:
            self.messages.critical(self, 'Server error', err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Error', LOST_CONNECTION_ERROR)
                self.close()
            self.messages.critical(self, 'Error', TIMEOUT_ERROR)
        else:
            self.storage.delete_contact(selected)
            self.clients_list_update()
            logger.info(f'Contact successfully deleted:  {selected}')
            self.messages.information(self, 'Success', 'Contact deleted')
            item.close()
            if selected == self.current_chat:
                self.current_chat = None
                self.set_disabled_input()

    @pyqtSlot(str)
    def new_message(self, sender):
        if sender == self.current_chat:
            self.history_list_update()
        else:
            if self.storage.contact_exists(sender):
                if self.messages.question(self, 'New message',
                                          f'Received new message from {sender}, '
                                          f'open chat?', QMessageBox.Yes,
                                          QMessageBox.No) == QMessageBox.Yes:
                    self.current_chat = sender
                    self.set_active_user()
            else:
                print('NO')
                if self.messages.question(self, 'New message',
                                          f'Received new message from {sender}.\n '
                                          f'User is not in your contact list\n'
                                          f' Add to contacts and open chat?',
                                          QMessageBox.Yes, QMessageBox.No) == QMessageBox.Yes:
                    self.add_contact(sender)
                    self.current_chat = sender
                    self.set_active_user()

    @pyqtSlot()
    def connection_lost(self):
        self.messages.warning(self, 'Connection error', LOST_CONNECTION_ERROR)
        self.close()

    def make_connection(self, trans_obj: GBChatClientTransport):
        trans_obj.new_message.connect(self.new_message)
        trans_obj.connection_lost.connect(self.connection_lost)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    db = ClientDBStorage('test')
    transport = GBChatClientTransport('127.0.0.1', 7777, db, 'test')
    window = ClientMainWindow(transport, db)
    sys.exit(app.exec_())
