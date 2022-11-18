import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from config import DSN

Base = declarative_base()


class Gender(Base):
    __tablename__ = "gender"
    id = sq.Column(sq.Integer, primary_key=True, unique=True)
    name = sq.Column(sq.String(length=40), unique=True)


class Status(Base):
    __tablename__ = "status"
    id = sq.Column(sq.Integer, primary_key=True, unique=True)
    name = sq.Column(sq.String(length=20))


class Account(Base):
    __tablename__ = "account"

    id = sq.Column(sq.Integer, primary_key=True)
    vk_id = sq.Column(sq.Integer, unique=True)
    name = sq.Column(sq.String(length=40))
    surname = sq.Column(sq.String(length=40))
    age = sq.Column(sq.Integer)
    gender_id = sq.Column(sq.Integer, sq.ForeignKey("gender.id"))
    city = sq.Column(sq.String(length=40))
    status = sq.Column(sq.Integer, sq.ForeignKey("status.id"))
    profile_link = sq.Column(sq.String(length=100))

    gender = relationship(Gender, backref='account')

    def __str__(self):
        return f'{self.id}: {self.name}'


class Photo(Base):
    __tablename__ = "photo"
    id = sq.Column(sq.Integer, primary_key=True)
    vk_id = sq.Column(sq.Integer, sq.ForeignKey("account.vk_id"), nullable=False)
    url = sq.Column(sq.String(length=100))

    photo = relationship(Account, backref='photo')

# дропаем все таблицы
def drop_tables(engine):
    Base.metadata.drop_all(engine)

# создаём все таблицы
def create_tables(engine):
    Base.metadata.create_all(engine)

# наполняем полами
def genderfiller(session, gender_list: list):
    for i in gender_list:
        gender = Gender(name=i)
        session.add(gender)
        session.commit()

# наполняем статусами
def statusfiller(session, status_list: list):
    for i in status_list:
        status = Status(name=i)
        session.add(status)
        session.commit()


if __name__ == '__main__':
    # Создаём движок
    engine = sq.create_engine(DSN)

    # Удаляем всё, если надо
    drop_tables(engine)

    # Создаём классы, то есть таблицы.
    create_tables(engine)

    # Открываем сессию
    Session = sessionmaker(bind=engine)
    session = Session()

    # Наполняем полами
    gender_list = ["Male", "Female"]
    genderfiller(session, gender_list)

    # Наполняем статусами
    status_list = ["unwatched", "watched", "favorite", "blacklist"]
    statusfiller(session, status_list)


    # Пример добавления
    account = Account(vk_id=1, name='Vladimir', surname='Putin', age=30, gender_id=1, city='St. Pet',
                      profile_link='www.leningrad.ru', status=1)
    session.add(account)
    session.commit()

    # если нужны данные cо статусами 1
    request = session.query(Account).filter_by(status=1).all()
    for i in request:
        print(i.name)

    # если нужно изменить данные в определенной записи
    request = session.query(Account).filter(account.id==1).one()
    request.status = 2
    print(request.status)


    # Закрываем сессию
    session.close()
