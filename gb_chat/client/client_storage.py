import datetime
import os
import sys

from sqlalchemy import create_engine, Table, Column, Integer, String, DateTime, MetaData, Text
from sqlalchemy.orm import mapper, sessionmaker

sys.path.append('..')

RECYCLE_PERIOD = 7200


class ClientDBStorage:
    class KnownUsers:
        known_user = None

        def __init__(self, user: str):
            self.known_user = user

    class MessageHistory:
        def __init__(self, user, direction, message):
            self.history_user = user
            self.history_direction = direction
            self.history_message = message
            self.history_date = datetime.datetime.now()

    class Contacts:
        contact_user = None

        def __init__(self, user: str):
            self.contact_user = user

    def __init__(self, user_name):
        db_path = os.path.dirname(os.path.realpath(__file__))
        db_file = f'client_{user_name}_db.sqlite'
        self.db_engine = create_engine(f'sqlite:///{os.path.join(db_path, db_file)}', echo=False,
                                       pool_recycle=RECYCLE_PERIOD, connect_args={'check_same_thread': False})
        self.metadata = MetaData()
        known_users_table = Table(
            'known_users',
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('known_user', String)
        )
        message_history_table = Table(
            'message_history',
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('history_user', String),
            Column('history_direction', String),
            Column('history_message', Text),
            Column('history_date', DateTime)
        )
        contacts_table = Table(
            'contacts',
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('contact_user', String, unique=True)
        )
        self.metadata.create_all(self.db_engine)
        mapper(self.KnownUsers, known_users_table)
        mapper(self.MessageHistory, message_history_table)
        mapper(self.Contacts, contacts_table)

        self.session = sessionmaker(bind=self.db_engine)()
        self.session.query(self.Contacts).delete()
        self.session.commit()

    def add_contact(self, contact_name):
        if not self.session.query(self.Contacts).filter_by(contact_user=contact_name).count():
            self.session.add(self.Contacts(contact_name))
            self.session.commit()

    def delete_contact(self, contact_name):
        self.session.query(self.Contacts).filter_by(contact_user=contact_name).delete()
        self.session.commit()

    def add_known_users(self, known_users_list):
        self.session.query(self.KnownUsers).delete()
        for user in known_users_list:
            self.session.add(self.KnownUsers(user))
        self.session.commit()

    def save_message(self, user, direction, message):
        self.session.add(self.MessageHistory(user, direction, message))
        self.session.commit()

    def get_contacts(self):
        return [current[0] for current in self.session.query(self.Contacts.contact_user).all()]

    def get_known_users(self):
        return [user[0] for user in self.session.query(self.KnownUsers.known_user).all()]

    def known_user_exists(self, user_name):
        return bool(self.session.query(self.KnownUsers).filter_by(known_user=user_name).count())

    def contact_exists(self, contact_name):
        return bool(self.session.query(self.Contacts).filter_by(contact_user=contact_name).count())

    def get_history(self, user):
        query = self.session.query(self.MessageHistory).filter_by(history_user=user)
        return [(row.history_user, row.history_direction, row.history_message, row.history_date) for row in query.all()]


if __name__ == '__main__':
    db = ClientDBStorage('test1')
    for i in ['test3', 'test4', 'test5']:
        db.add_contact(i)
    db.add_contact('test4')
    db.add_known_users(['test1', 'test2', 'test3', 'test4', 'test5'])
    db.save_message('test2', 'in', f'Test message. {datetime.datetime.now()}!')
    db.save_message('test2', 'out', f'Another test message. {datetime.datetime.now()}!')
    print(db.get_contacts())
    print(db.get_known_users())
    print(db.known_user_exists('test1'))
    print(db.known_user_exists('test10'))
    print(sorted(db.get_history('test2'), key=lambda item: item[3]))
    db.delete_contact('test4')
    print(db.get_contacts())
