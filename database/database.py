import sqlalchemy as sq
from sqlalchemy.orm import declarative_base

Base = declarative_base()


def drop_tables(engine) -> None:
    Base.metadata.drop_all(engine)


def create_tables(engine) -> None:
    Base.metadata.create_all(engine)

def status_filler(session) -> None:
    session.add(Status(name='favorite'))
    session.add(Status(name='black list'))
    session.commit()

class Status(Base):
    __tablename__ = 'status'
    id = sq.Column(sq.Integer, primary_key=True)
    name = sq.Column(sq.String(length=40), unique=True)


class User(Base):
    __tablename__ = 'user'
    id = sq.Column(sq.Integer, primary_key=True)
    vk_id = sq.Column(sq.Integer, unique=True)


class Preferences(Base):
    __tablename__ = 'preferences'
    id = sq.Column(sq.Integer, primary_key=True)
    vk_id = sq.Column(sq.Integer, sq.ForeignKey('user.vk_id'))
    watched_vk_id = sq.Column(sq.Integer)
    status_id = sq.Column(sq.Integer, sq.ForeignKey('status.id'))



if __name__ == '__main__':
    pass