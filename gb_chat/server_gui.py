import sys
import threading

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QLabel, QTableView, QApplication, QDialog, QPushButton, \
    QLineEdit, QFileDialog

from server.server_storage import ServerDBStorage


db_lock = threading.Lock()


def get_active_users_model(db: ServerDBStorage) -> QStandardItemModel:
    result = QStandardItemModel()
    result.setHorizontalHeaderLabels(['Client name', 'IP address', 'Port', 'Date'])
    with db_lock:
        query = db.current_users_list()
    for name, ip, port, date in query:
        user = QStandardItem(name)
        user_ip = QStandardItem(ip)
        user_port = QStandardItem(port)
        user_date = QStandardItem(str(date.replace(microsecond=0)))
        user.setEditable(False)
        user_ip.setEditable(False)
        user_port.setEditable(False)
        user_date.setEditable(False)
        result.appendRow([user, user_ip, user_port, user_date])
    return result


def get_history_model(db: ServerDBStorage) -> QStandardItemModel:
    result = QStandardItemModel()
    result.setHorizontalHeaderLabels(['Client name', 'Last login', 'Messages sent', 'Messages received'])
    with db_lock:
        query = db.message_history_list()
    for entry in query:
        user, date, sent, received = entry
        user_item = QStandardItem(user)
        date_item = QStandardItem(str(date.replace(microsecond=0)))
        sent_item = QStandardItem(str(sent))
        received_item = QStandardItem(str(received))
        user_item.setEditable(False)
        date_item.setEditable(False)
        sent_item.setEditable(False)
        received_item.setEditable(False)
        result.appendRow([user_item, date_item, sent_item, received_item])
    return result


class ServerGUIMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.exit_action = QAction('Exit', self)
        self.exit_action.setShortcut('Ctrl+Q')
        self.exit_action.triggered.connect(qApp.quit)

        self.refresh_button = QAction('Refresh list', self)
        self.history_button = QAction('Users history', self)
        self.settings_button = QAction('Server settings', self)

        self.statusBar()

        self.toolbar = self.addToolBar('MainBar')
        self.toolbar.addAction(self.exit_action)
        self.toolbar.addAction(self.refresh_button)
        self.toolbar.addAction(self.history_button)
        self.toolbar.addAction(self.settings_button)

        self.setFixedSize(800, 600)
        self.setWindowTitle('GB Chat server')

        self.label = QLabel('Current active clients:', self)
        self.label.setFixedSize(400, 15)
        self.label.move(10, 35)

        self.active_clients_table = QTableView(self)
        self.active_clients_table.move(10, 55)
        self.active_clients_table.setFixedSize(780, 400)

        self.show()


class ServerGUIHistoryWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Clients stats')
        self.setFixedSize(600, 700)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.close_button = QPushButton('Close', self)
        self.close_button.move(250, 650)
        self.close_button.clicked.connect(self.close)

        self.history_table = QTableView(self)
        self.history_table.move(10, 10)
        self.history_table.setFixedSize(580, 620)

        self.show()


class ServerGUIConfigWindow(QDialog):
    def __init__(self):
        super().__init__()

        self.setFixedSize(365, 260)
        self.setWindowTitle('Server settings')

        self.db_path_label = QLabel('Database file path: ', self)
        self.db_path_label.move(10, 10)
        self.db_path_label.setFixedSize(240, 15)

        self.db_path = QLineEdit(self)
        self.db_path.setFixedSize(250, 20)
        self.db_path.move(10, 30)
        self.db_path.setReadOnly(True)

        self.db_path_select = QPushButton('Browse', self)
        self.db_path_select.move(275, 28)

        def open_file_dialog():
            # global dialog
            dialog = QFileDialog(self)
            path = dialog.getExistingDirectory()
            path = path.replace('/', '\\')
            self.db_path.insert(path)

        self.db_path_select.clicked.connect(open_file_dialog)
        self.db_file_label = QLabel('Database file name: ', self)
        self.db_file_label.move(10, 68)
        self.db_file_label.setFixedSize(180, 15)

        self.db_file = QLineEdit(self)
        self.db_file.move(200, 66)
        self.db_file.setFixedSize(150, 20)

        self.port_label = QLabel('Connection port:', self)
        self.port_label.move(10, 108)
        self.port_label.setFixedSize(180, 15)

        self.port = QLineEdit(self)
        self.port.move(200, 108)
        self.port.setFixedSize(150, 20)

        self.ip_label = QLabel('IP listen address:', self)
        self.ip_label.move(10, 148)
        self.ip_label.setFixedSize(180, 15)

        self.ip_label_note = QLabel(' leave blank to accept any', self)
        self.ip_label_note.move(10, 168)
        self.ip_label_note.setFixedSize(500, 30)

        self.ip = QLineEdit(self)
        self.ip.move(200, 148)
        self.ip.setFixedSize(150, 20)

        self.save_btn = QPushButton('Save', self)
        self.save_btn.move(190, 220)

        self.close_button = QPushButton('Close', self)
        self.close_button.move(275, 220)
        self.close_button.clicked.connect(self.close)

        self.show()


if __name__ == '__main__':
    # Main window check

    # app = QApplication(sys.argv)
    # main_window = ServerGUIMainWindow()
    # main_window.statusBar().showMessage('Hooray, i am a status bar!!!')
    # users_list = QStandardItemModel(main_window)
    # users_list.setHorizontalHeaderLabels(['Name', 'IP Address', 'Port', 'Date'])
    # users_list.appendRow(
    #     [QStandardItem('test-1'), QStandardItem('172.16.0.2'), QStandardItem('7777'), QStandardItem('10:10:10')])
    # users_list.appendRow(
    #     [QStandardItem('test-2'), QStandardItem('192.168.0.10'), QStandardItem('8888'), QStandardItem('10:10:11')])
    # users_list.appendRow(
    #     [QStandardItem('test-3'), QStandardItem('10.10.0.23'), QStandardItem('9999'), QStandardItem('12:10:10')])
    # main_window.active_clients_table.setModel(users_list)
    # main_window.active_clients_table.resizeColumnsToContents()
    # main_window.active_clients_table.resizeRowsToContents()
    # app.exec_()

    # History window check

    app = QApplication(sys.argv)
    window = ServerGUIHistoryWindow()
    history_list = QStandardItemModel(window)
    history_list.setHorizontalHeaderLabels(
        ['Name', 'Last login', 'Sent', 'Received'])
    history_list.appendRow(
        [QStandardItem('test-1'), QStandardItem('10:10:10'), QStandardItem('2'), QStandardItem('3')])
    history_list.appendRow(
        [QStandardItem('test-2'), QStandardItem('20:10:12'), QStandardItem('8'), QStandardItem('5')])
    window.history_table.setModel(history_list)
    window.history_table.resizeColumnsToContents()

    app.exec_()

    # Settings window check

    # app = QApplication(sys.argv)
    # _ = ServerGUIConfigWindow()
    # app.exec_()
