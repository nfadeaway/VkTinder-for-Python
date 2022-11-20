import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
# from config import DSN

Base = declarative_base()


class Genders(Base):
    __tablename__ = 'genders'
    gender_id = sq.Column(sq.Integer, primary_key=True)
    gender_name = sq.Column(sq.String(length=20), unique=True)


# class Status(Base):
#     __tablename__ = 'status'
#     status_id = sq.Column(sq.Integer, primary_key=True, unique=True)
#     status_name = sq.Column(sq.String(length=20))


class Accounts(Base):
    __tablename__ = 'accounts'

    account_id = sq.Column(sq.Integer, primary_key=True)
    vk_id = sq.Column(sq.Integer, unique=True)
    name = sq.Column(sq.String(length=40))
    surname = sq.Column(sq.String(length=40))
    age = sq.Column(sq.Integer)
    gender_id = sq.Column(sq.Integer, sq.ForeignKey('genders.gender_id'))
    city_id = sq.Column(sq.Integer)
    city_title = sq.Column(sq.String(length=40))
    status = sq.Column(sq.String(length=30))
    profile_link = sq.Column(sq.String(length=100))

    gender = relationship(Genders, backref='accounts')

    def __str__(self):
        return f'ID: {self. account_id}, VK_ID{self.vk_id}, Name:{self.name}, Surname:{self.surname}, ' \
               f'Age:{self.age}, Gender_id:{self.gender_id}, City_id:{self.city_id}, City_name:{self.city_name}, ' \
               f'Status_id:{self.status_id} Profile_link:{self.profile_link}'


class Photos(Base):
    __tablename__ = 'photos'
    photo_id = sq.Column(sq.Integer, primary_key=True)
    vk_id = sq.Column(sq.Integer, sq.ForeignKey('accounts.vk_id'), nullable=False)
    photo_attachment = sq.Column(sq.String(length=200))

    accounts = relationship(Accounts, backref='photos')


# дропаем все таблицы
def drop_tables(engine) -> None:
    Base.metadata.drop_all(engine)


# создаём все таблицы
def create_tables(engine) -> None:
    Base.metadata.create_all(engine)
    print('Таблицы созданы')


# наполняем полами
def gender_filler(session) -> None:
    session.add(Genders(gender_name='женский'))
    session.add(Genders(gender_name='мужской'))
    session.commit()


# наполняем статусами
def status_filler(session, status_list: list) -> None:
    for i in status_list:
        status = Status(name=i)
        session.add(status)
        session.commit()


# смена статуса по VK_ID
def status_changer(session, vk_id: int, new_status: str) -> None:
    request = session.query(Accounts).filter(Accounts.vk_id == vk_id).one()
    request.status = new_status
    session.commit()


# if __name__ == '__main__':
#     # Создаём движок
#     engine = sq.create_engine(DSN)
#
#     # Удаляем всё, если надо
#     drop_tables(engine)
#
#     # Создаём классы, то есть таблицы.
#     create_tables(engine)
#
#     # Открываем сессию
#     Session = sessionmaker(bind=engine)
#     session = Session()
#
#     # Наполняем полами
#     gender_list = ["Male", "Female"]
#     gender_filler(session, gender_list)
#
#     # Наполняем статусами
#     status_list = ["unwatched", "watched", "favorite", "blacklist"]
#     status_filler(session, status_list)
#
#     # Пример добавления
#     account = Accounts(vk_id=1, name='Vladimir', surname='Putin', age=30, gender_id=1, city='St. Pet',
#                       profile_link='www.leningrad.ru', status_id=1)
#     session.add(account)
#     session.commit()
#
#     # если нужны данные cо статусами 1
#     request = session.query(Accounts).filter_by(status_id=1).all()
#     for i in request:
#         pass
#
#     #если нужна одна запись
#     request = session.query(Accounts).filter_by(status_id=1).one()
#
#     # если нужно изменить данные в определенной записи
#     status_changer(session, vk_id=1, new_status_id=2)
#
#     # Закрываем сессию
#     session.close()
