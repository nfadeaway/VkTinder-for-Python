from sqlalchemy.orm import sessionmaker

import database.models
from database.models import *
from dotenv import load_dotenv
import os

load_dotenv()

class DB:

    def __init__(self):
        self.Base = database.models.Base
        self.engine = sq.create_engine(os.getenv('DSN'))
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def drop_tables(self) -> None:
        self.Base.metadata.drop_all(self.engine)

    def create_tables(self) -> None:
        self.Base.metadata.create_all(self.engine)

    def status_filler(self) -> None:
        self.session.add(Status(name='favorite'))
        self.session.add(Status(name='black list'))
        self.session.commit()

    def check_user(self, self_id) -> None:
        user = self.session.query(User).filter_by(vk_id=self_id).all()
        if not user:
            self.session.add(User(vk_id=self_id))
            self.session.commit()

    def request_preferences(self, self_id, user_id) -> list:
        return self.session.query(Preferences).filter_by(vk_id=self_id, watched_vk_id=user_id).all()

    def add_favorite(self, self_id, user_id):
        self.session.add(Preferences(vk_id=self_id, watched_vk_id=user_id, status_id=1))
        self.session.commit()

    def add_blacklist(self, self_id, user_id):
        self.session.add(Preferences(vk_id=self_id, watched_vk_id=user_id, status_id=2))
        self.session.commit()

    def request_favorite_list(self, self_id) -> list:
        return self.session.query(Preferences).filter_by(vk_id=self_id, status_id=1).all()
