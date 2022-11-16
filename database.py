import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from config import DSN

Base = declarative_base()


class Gender(Base):
    __tablename__ = "gender"
    id = sq.Column(sq.Integer, primary_key=True)
    name = sq.Column(sq.String(length=40), unique=True)


class Account(Base):
    __tablename__ = "account"

    id = sq.Column(sq.Integer, primary_key=True)
    vk_id = sq.Column(sq.Integer)
    name = sq.Column(sq.String(length=40))
    surname = sq.Column(sq.String(length=40))
    age = sq.Column(sq.Integer)
    gender_id = sq.Column(sq.Integer, sq.ForeignKey("gender.id"))
    city = sq.Column(sq.String(length=40), unique=True)
    profile_link = sq.Column(sq.String(length=100))

    gender = relationship(Gender, backref='account')


class Photo(Base):
    __tablename__ = "photo"
    id = sq.Column(sq.Integer, primary_key=True)
    vk_id = sq.Column(sq.Integer, sq.ForeignKey("account.vk_id"), nullable=False)
    url = sq.Column(sq.String(length=100))

    account_photo = relationship(Account, backref='photo')


class Favorite(Base):
    __tablename__ = "favorite"
    id = sq.Column(sq.Integer, primary_key=True)
    vk_id = sq.Column(sq.Integer, sq.ForeignKey("account.vk_id"))

    account_favorite = relationship(Account, backref='favorite')


class Blacklist(Base):
    __tablename__ = "blacklist"
    id = sq.Column(sq.Integer, primary_key=True)
    vk_id = sq.Column(sq.Integer, sq.ForeignKey("account.vk_id"))

    account_blacklist = relationship(Account, backref="blacklist")


def drop_tables(engine):
    Base.metadata.drop_all(engine)


def create_tables(engine):
    Base.metadata.create_all(engine)


if __name__ == '__main__':
    # Создаём движок
    engine = sq.create_engine(DSN)

    # Удаляем всё, если надо =)
    drop_tables(engine)

    # Создаём классы, тоесть таблицы.
    create_tables(engine)

    # Открываем сессию
    Session = sessionmaker(bind=engine)
    session = Session()

    # Наполняем
    # gender = Gender(name='Male')
    # # account = Account(vk_id=1, name='Vladimir', surname='Putin', age=30, gender_id=1, city='St. Pet',
    # #                   profile_link='www.leningrad.ru')
    # session.add(gender)
    # # session.add(account)
    # session.commit()

    # Закрываем сессию
    session.close()