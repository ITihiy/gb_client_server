import datetime
from pprint import pprint

from sqlalchemy import create_engine, Table, Column, Integer, String, DateTime, ForeignKey, MetaData
from sqlalchemy.orm import mapper, sessionmaker

RECYCLE_PERIOD = 7200


class ServerDBStorage:
    class AllUsers:
        id = None
        user_name = None
        last_login_time = None

        def __init__(self, user_name: str):
            self.user_name = user_name
            self.last_login_time = datetime.datetime.now()

        def __repr__(self):
            return f'User name: {self.user_name}\nLast login: {self.last_login_time}'

    class CurrentActiveUsers:
        current_user_address = None
        current_user_port = None
        current_user_login_time = None

        def __init__(self, user_id, user_address, user_port, user_login_time):
            self.current_user_id = user_id
            self.current_user_address = user_address
            self.current_user_port = user_port
            self.current_user_login_time = user_login_time

    class LoginHistory:
        history_login_time = None
        history_user_address = None
        history_user_port = None

        def __init__(self, user_id, user_login_time, user_address, user_port):
            self.history_user = user_id
            self.history_login_time = user_login_time
            self.history_user_address = user_address
            self.history_user_port = user_port

    class UserContacts:
        contact_user = None
        contact_contact = None

        def __init__(self, user_id, contact_id):
            self.contact_user = user_id
            self.contact_contact = contact_id

    class UserMessageHistory:
        message_history_sent = None
        message_history_received = None

        def __init__(self, user_id):
            self.message_history_user = user_id
            self.message_history_sent = 0
            self.message_history_received = 0

    def __init__(self, db_path):
        self.db_engine = create_engine(f'sqlite:///{db_path}', echo=False, pool_recycle=RECYCLE_PERIOD,
                                       connect_args={'check_same_thread': False})
        self.metadata = MetaData()

        all_users_table = Table(
            'all_users',
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('user_name', String(50), unique=True),
            Column('last_login_time', DateTime),
        )

        current_users_table = Table(
            'current_users',
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('current_user_id', ForeignKey('all_users.id'), unique=True),
            Column('current_user_address', String(15)),
            Column('current_user_port', String(5)),
            Column('current_user_login_time', DateTime)
        )

        users_history_table = Table(
            'users_history',
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('history_user', ForeignKey('all_users.id')),
            Column('history_login_time', DateTime),
            Column('history_user_address', String(15)),
            Column('history_user_port', String(5))
        )

        user_contacts_table = Table(
            'user_contacts',
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('contact_user', ForeignKey('all_users.id')),
            Column('contact_contact', ForeignKey('all_users.id'))
        )

        message_history_table = Table(
            'message_history',
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('message_history_user', ForeignKey('all_users.id')),
            Column('message_history_sent', Integer),
            Column('message_history_received', Integer)
        )

        mapper(self.AllUsers, all_users_table)
        mapper(self.CurrentActiveUsers, current_users_table)
        mapper(self.LoginHistory, users_history_table)
        mapper(self.UserContacts, user_contacts_table)
        mapper(self.UserMessageHistory, message_history_table)

        self.metadata.create_all(self.db_engine)

        self.session = sessionmaker(bind=self.db_engine)()
        self.session.query(self.CurrentActiveUsers).delete()
        self.session.commit()

    def login_user(self, user_name, user_address, user_port):
        query_result = self.session.query(self.AllUsers).filter_by(user_name=user_name)
        if query_result.count():
            current_user = query_result.first()
            current_user.last_login = datetime.datetime.now()
        else:
            current_user = self.AllUsers(user_name)
            self.session.add(current_user)
            self.session.commit()
            self.session.add(self.UserMessageHistory(current_user.id))
        self.session.add(self.CurrentActiveUsers(current_user.id, user_address, user_port, datetime.datetime.now()))
        self.session.add(self.LoginHistory(current_user.id, datetime.datetime.now(), user_address, user_port))
        self.session.commit()

    def logout_user(self, user_name):
        current_user = self.session.query(self.AllUsers).filter_by(user_name=user_name).first()
        self.session.query(self.CurrentActiveUsers).filter_by(current_user_id=current_user.id).delete()
        self.session.commit()

    def message_history_update(self, from_user, to_user):
        from_user = self.session.query(self.AllUsers).filter_by(user_name=from_user).first().id
        to_user = self.session.query(self.AllUsers).filter_by(user_name=to_user).first().id
        sender_row = self.session.query(self.UserMessageHistory).filter_by(message_history_user=from_user).first()
        sender_row.message_history_sent += 1
        recipient_row = self.session.query(self.UserMessageHistory).filter_by(message_history_user=to_user).first()
        recipient_row.message_history_received += 1
        self.session.commit()

    def all_users_list(self):
        return self.session.query(self.AllUsers.user_name, self.AllUsers.last_login_time).all()

    def current_users_list(self):
        return self.session.query(
            self.AllUsers.user_name,
            self.CurrentActiveUsers.current_user_address,
            self.CurrentActiveUsers.current_user_port,
            self.CurrentActiveUsers.current_user_login_time
        ).join(self.AllUsers).all()

    def history_list(self, user_name=None):
        query = self.session.query(
            self.AllUsers.user_name,
            self.LoginHistory.history_login_time,
            self.LoginHistory.history_user_address,
            self.LoginHistory.history_user_port
        ).join(self.AllUsers)
        if user_name:
            query = query.filter(self.AllUsers.user_name == user_name)
        return query.all()

    def message_history_list(self):
        return self.session.query(
            self.AllUsers.user_name,
            self.AllUsers.last_login_time,
            self.UserMessageHistory.message_history_sent,
            self.UserMessageHistory.message_history_received
        ).join(self.AllUsers).all()

    def add_contact(self, user, contact):
        current_user = self.session.query(self.AllUsers).filter_by(user_name=user).first()
        current_contact = self.session.query(self.AllUsers).filter_by(user_name=contact).first()
        if not current_user or not current_contact or self.session.query(self.UserContacts).filter_by(
                contact_user=current_user.id,
                contact_contact=current_contact.id).count():
            return
        self.session.add(self.UserContacts(current_user.id, current_contact.id))
        self.session.commit()

    def delete_contact(self, user, contact):
        current_user = self.session.query(self.AllUsers).filter_by(user_name=user).first()
        current_contact = self.session.query(self.AllUsers).filter_by(user_name=contact).first()
        if not current_user or current_contact:
            return
        self.session.query(self.UserContacts).filter(self.UserContacts.contact_user == current_user.id,
                                                     self.UserContacts.contact_contact == current_contact.id).delete()
        self.session.commit()

    def get_all_contacts(self, user):
        current_user = self.session.query(self.AllUsers).filter_by(user_name=user).first()
        query = self.session.query(self.UserContacts, self.AllUsers.user_name).filter_by(
            contact_user=current_user.id).join(self.AllUsers, self.UserContacts.contact_contact == self.AllUsers.id)
        return [entry[1] for entry in query.all()]


if __name__ == '__main__':
    db = ServerDBStorage('server_db.sqlite')
    db.login_user('1111', '192.168.1.113', 8080)
    db.login_user('McG2', '192.168.1.113', 8081)
    db.login_user('test1', '192.168.1.113', 8080)
    db.login_user('test2', '192.168.1.113', 8081)
    db.login_user('test3', '192.168.1.113', 8080)
    pprint(db.all_users_list())
    pprint(db.current_users_list())
    db.logout_user('McG2')
    pprint(db.history_list('re'))
    db.add_contact('test2', 'test1')
    db.add_contact('test1', 'test3')
    db.add_contact('test1', 'test6')
    db.delete_contact('test1', 'test3')
    db.message_history_update('McG2', '1111')
    pprint(db.message_history_list())
    pprint(db.get_all_contacts('test1'))
