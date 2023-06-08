import os
import json
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


engine = create_engine('sqlite:///kivydatabase.db')
Base = declarative_base()


SESSION_FILE = 'JSON_files/session_state.json'


def save_session(user_id):
    with open(SESSION_FILE, 'w') as f:
        json.dump({'user_id': user_id}, f)


def load_session():
    try:
        with open(SESSION_FILE, 'r') as f:
            data = json.load(f)
            if data:
                return data['user_id']
            return None
    except FileNotFoundError:
        return None


class User(Base):
    """таблица Uesrs в базе данных"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String)
    password = Column(String)
    is_admin = Column(Boolean)


Base.metadata.create_all(engine)


def create_folder(id):
    # создание папки юзера
    user_folder = f'user_{id}'
    os.makedirs(user_folder)


def add_user(username, password, is_admin=False):
    """функция добавления пользователя в БД"""
    Session = sessionmaker(bind=engine)
    session = Session()

    new_user = User(username=username, password=password, is_admin=is_admin)
    session.add(new_user)
    session.commit()


    create_folder(new_user.id)
    session.close()


def delete_user(user_id):
    """функция удаления пользователя из БД"""
    Session = sessionmaker(bind=engine)
    session = Session()
    user = session.query(User).get(user_id)
    if user:
        session.delete(user)
        session.commit()
    session.close()