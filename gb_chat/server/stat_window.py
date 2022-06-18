from PyQt5.QtWidgets import QDialog, QPushButton, QTableView
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt


class StatWindow(QDialog):
    def __init__(self, database):
        super().__init__()

        self.storage = database
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Clients statistics')
        self.setFixedSize(600, 700)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.close_button = QPushButton('Close', self)
        self.close_button.move(250, 650)
        self.close_button.clicked.connect(self.close)

        self.stat_table = QTableView(self)
        self.stat_table.move(10, 10)
        self.stat_table.setFixedSize(580, 620)

        self.create_stat_model()

    def create_stat_model(self):
        stat_list = self.storage.message_history_list()

        list_ = QStandardItemModel()
        list_.setHorizontalHeaderLabels(['Name', 'Last login', 'Sent', 'Received'])
        for user, last_seen, sent, recvd in stat_list:
            user = QStandardItem(user)
            user.setEditable(False)
            last_seen = QStandardItem(str(last_seen.replace(microsecond=0)))
            last_seen.setEditable(False)
            sent = QStandardItem(str(sent))
            sent.setEditable(False)
            recvd = QStandardItem(str(recvd))
            recvd.setEditable(False)
            list_.appendRow([user, last_seen, sent, recvd])
        self.stat_table.setModel(list_)
        self.stat_table.resizeColumnsToContents()
        self.stat_table.resizeRowsToContents()