import datetime

from sqlalchemy import create_engine, Table, Column, Integer, String, DateTime, ForeignKey, MetaData
from sqlalchemy.orm import mapper, sessionmaker

SERVER_DB = 'sqlite:///server_db.sqlite'
RECYCLE_PERIOD = 7200


class ServerDBStorage:
    class AllUsers:
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

    def __init__(self):
        self.db_engine = create_engine(SERVER_DB, echo=False, pool_recycle=RECYCLE_PERIOD)
        self.metadata = MetaData()

        all_users_table = Table(
            'all_users',
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('user_name', String(50)),
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

        mapper(self.AllUsers, all_users_table)
        mapper(self.CurrentActiveUsers, current_users_table)
        mapper(self.LoginHistory, users_history_table)

        self.metadata.create_all(self.db_engine)

        Session = sessionmaker(bind=self.db_engine)
        self.session = Session()
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
        self.session.add(self.CurrentActiveUsers(current_user.id, user_address, user_port, datetime.datetime.now()))
        self.session.add(self.LoginHistory(current_user.id, datetime.datetime.now(), user_address, user_port))
        self.session.commit()

    def logout_user(self, user_name):
        current_user = self.session.query(self.AllUsers).filter_by(user_name=user_name).first()
        self.session.query(self.CurrentActiveUsers).filter_by(current_user_id=current_user.id).delete()
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


if __name__ == '__main__':
    storage = ServerDBStorage()
