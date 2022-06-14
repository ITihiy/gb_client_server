import datetime

from sqlalchemy import create_engine, Table, Column, Integer, String, DateTime, MetaData, Text
from sqlalchemy.orm import mapper, sessionmaker

RECYCLE_PERIOD = 7200


class ClientDBStorage:
    class KnownUsers:
        known_user_name = None

        def __init__(self, user_name: str):
            self.known_user_name = user_name

    class MessageHistory:
        def __init__(self, from_user, to_user, message):
            self.history_from_user = from_user
            self.history_to_user = to_user
            self.history_message = message
            self.history_date = datetime.datetime.now()

    class Contacts:
        contact_user_name = None

        def __init__(self, user_name):
            self.contact_user_name = user_name

    def __init__(self, user_name):
        self.db_engine = create_engine(f'sqlite:///client_{user_name}_db.sqlite', echo=False,
                                       pool_recycle=RECYCLE_PERIOD, connect_args={'check_same_thread': False})
        self.metadata = MetaData()
        known_users_table = Table(
            'known_users',
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('known_user_name', String)
        )
        message_history_table = Table(
            'message_history',
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('history_from_user', String),
            Column('history_to_user', String),
            Column('history_message', Text),
            Column('history_date', DateTime)
        )
        contacts_table = Table(
            'contacts',
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('contact_user_name', String, unique=True)
        )
        self.metadata.create_all(self.db_engine)
        mapper(self.KnownUsers, known_users_table)
        mapper(self.MessageHistory, message_history_table)
        mapper(self.Contacts, contacts_table)

        self.session = sessionmaker(bind=self.db_engine)()
        self.session.query(self.Contacts).delete()
        self.session.commit()

    def add_contact(self, contact_name):
        if not self.session.query(self.Contacts).filter_by(contact_user_name=contact_name).count():
            self.session.add(self.Contacts(contact_name))
            self.session.commit()

    def delete_contact(self, contact_name):
        self.session.query(self.Contacts).filter_by(contact_user_name=contact_name).delete()
        self.session.commit()

    def add_known_users(self, known_users_list):
        self.session.query(self.KnownUsers).delete()
        for user in known_users_list:
            self.session.add(self.KnownUsers(user))
        self.session.commit()

    def save_message(self, from_user, to_user, message):
        self.session.add(self.MessageHistory(from_user, to_user, message))
        self.session.commit()

    def get_contacts(self):
        return [current[0] for current in self.session.query(self.Contacts.contact_user_name).all()]

    def get_known_users(self):
        return [user[0] for user in self.session.query(self.KnownUsers.known_user_name).all()]

    def known_user_exists(self, user_name):
        return bool(self.session.query(self.KnownUsers).filter_by(known_user_name=user_name).count())

    def contact_exists(self, contact_name):
        return bool(self.session.query(self.Contacts).filter_by(contact_user_name=contact_name).count())

    def get_history(self, from_user=None, to_user=None):
        query_result = self.session.query(self.MessageHistory)
        if from_user:
            query_result = query_result.filter_by(history_from_user=from_user)
        if to_user:
            query_result = query_result.filter_by(history_to_user=to_user)
        return [(entry.history_from_user, entry.history_to_user, entry.history_message, entry.history_date) for entry in
                query_result.all()]


if __name__ == '__main__':
    storage = ClientDBStorage('Alex')
    for contact in ['Mary', 'Bob', 'John', 'Anna']:
        storage.add_contact(contact)
    storage.add_contact('John')
    storage.add_known_users(['Alex', 'Mary', 'Bob', 'John', 'Anna'])
    storage.save_message('Alex', 'John', 'Hello from Alex to John.')
    storage.save_message('Mary', 'Bob', 'Hi. from Mary to Bob.')

    print(storage.get_known_users())
    print(storage.get_contacts())

    print(storage.contact_exists('Mary'))
    print(storage.contact_exists('Tom'))

    print(storage.known_user_exists('Mary'))
    print(storage.known_user_exists('Tom'))

    print(storage.get_history('Alex'))
    print(storage.get_history(to_user='Bob'))

    storage.delete_contact('Anna')
    print(storage.get_contacts())
