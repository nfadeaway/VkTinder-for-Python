import sqlalchemy
import psycopg2
from dotenv import load_dotenv
import os
from database.database import drop_tables, create_tables, gender_filler, id_filler, Accounts, Photos, status_changer
from sqlalchemy.orm import sessionmaker

from vk.vk import VK, preview_photos
from vk_api.longpoll import VkEventType
import datetime
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

load_dotenv()

def main():
    # Все настройки хранятся в файле .env в папке с модулем main.py
    # USER_TOKEN='ТОКЕН'
    # GROUP_TOKEN='GROUP_TOKEN'
    # DSN='postgresql://postgres:55555@localhost:5432/vkinder'
    vkinder_user = VK(os.getenv("USER_TOKEN"), os.getenv("GROUP_TOKEN"))
    engine = sqlalchemy.create_engine(os.getenv('DSN'))

    # Создаем таблицы, сессию
    drop_tables(engine)
    create_tables(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    # Заполняем таблицу gender
    gender_filler(session)

    # Создаем 2 клавиатуры - "начальная" и рабочая
    welcome_keyboard = VkKeyboard(one_time=True)
    welcome_keyboard.add_button(label="Начать", color=VkKeyboardColor.POSITIVE)
    regular_keyboard = VkKeyboard()
    regular_keyboard.add_button(label="В ЧС", color=VkKeyboardColor.NEGATIVE)
    regular_keyboard.add_button(label="В избранное", color=VkKeyboardColor.POSITIVE)
    regular_keyboard.add_button(label="Дальше", color=VkKeyboardColor.PRIMARY)
    regular_keyboard.add_line()
    regular_keyboard.add_button(label="Показать избранное", color=VkKeyboardColor.SECONDARY)

    welcome_msg_flag = 0  # Флаг проверки входа программы в основной режим работы
    black_list_flag = 0  # Флаг проверки статуса записи о пользователе на blacklist
    favorites_list_flag = 0  # Флаг проверки статуса записи о пользователе на favorites
    age_step = -3  # Настройка шага поиска людей по возрасту от -3 лет от текущего возраста до +3 лет

    for event in vkinder_user.longpool.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            if welcome_msg_flag == 0:
                incoming_msg = event.text.lower()
                vkinder_user_id = event.user_id
                vkinder_user_info = vkinder_user.profile_info(vkinder_user_id)
                vkinder_user_name = vkinder_user_info['name']
                vkinder_user_city = vkinder_user_info['city']
                vkinder_user_city_title = vkinder_user_info['city_title']
                vkinder_user_sex = vkinder_user_info['sex']
                vkinder_user_age = vkinder_user_info['age']
                id_filler(session, vkinder_user_id)

                # Обрабатываем отсутствие даты рождения у пользователя VKinder
                if vkinder_user_age == '':
                    vkinder_user.send_some_msg(vkinder_user_id, f'Добро пожаловать в VKinder!\n'
                                                                f'Мы проверили твои данные и обнаружили, что не знаем, '
                                                                f'сколько тебе лет!\n '
                                                                f'Напиши, пожалуйста, сколько тебе лет?')
                else:
                    vkinder_user.send_some_msg(vkinder_user_id,
                                               f'Добро пожаловать в VKinder!\n'
                                               f'Мы проверили твои данные и нашли всё необходимое.\n'
                                               f'Можем начинать!',
                                               welcome_keyboard.get_keyboard())
                welcome_msg_flag = 1
                continue

            # Обработка команд пользователя VKinder
            if welcome_msg_flag == 1:
                incoming_msg = event.text.lower()
                if vkinder_user_age == '' and incoming_msg.isdigit():
                    vkinder_user_age = incoming_msg
                    vkinder_user.send_some_msg(vkinder_user_id, 'Данные записаны!',  welcome_keyboard.get_keyboard())
                    continue

                elif incoming_msg == 'я':
                    vkinder_user.send_some_msg(vkinder_user_id,
                                               f'Имя {vkinder_user_name},\n'
                                               f'Возраст {vkinder_user_age},\n'
                                               f'Пол {vkinder_user_sex},\n'
                                               f'Код города {vkinder_user_city},\n'
                                               f'Название города {vkinder_user_city_title}',
                                               )
                    continue

                elif incoming_msg == 'начать':
                    vkinder_user.send_some_msg(vkinder_user_id, 'Начинаем поиск! Подождите немного..')
                    # Ищем людей по фильтру
                    found_users = []
                    while age_step < 3:
                        found_users.extend(vkinder_user.user_search('1000', vkinder_user_city, vkinder_user_sex,
                                                                    vkinder_user_age, age_step)['items'])
                        age_step += 1

                    # Обрабатываем и выдаем найденных людей, перед выдачей проверяем на наличие записи в блек-листе
                    # и иные проблемы (несовпадение города, закрытый профиль, отсутствие даты рождения)
                    for user in found_users:
                        request_blacklist = session.query(Accounts).filter_by(status='blacklist').all()
                        for row in request_blacklist:
                            if user['id'] == row.vk_id:
                                black_list_flag = 1
                                break
                        if black_list_flag:
                            black_list_flag = 0
                            vkinder_user.send_some_msg(vkinder_user_id, 'Найденный пользователь в '
                                                                        'блек-листе, продолжаем!')
                            continue
                        elif 'city' not in user:
                            continue
                        elif not user['is_closed'] and str(user['city']['id']) == vkinder_user_city and len(
                                user['bdate'].split('.')) == 3:
                            user_photo_list = vkinder_user.get_photo(user['id'])
                            if user_photo_list['count'] > 2:
                                user_photos = preview_photos(user_photo_list)
                                vkinder_user.send_some_msg(vkinder_user_id,
                                                           f'{user["first_name"]} {user["last_name"]}\n'
                                                           f'https://vk.com/id{user["id"]}\n',
                                                           regular_keyboard.get_keyboard(),
                                                           f'photo{user["id"]}_{user_photos[0][0]},'
                                                           f'photo{user["id"]}_{user_photos[1][0]},'
                                                           f'photo{user["id"]}_{user_photos[2][0]}')
                            else:
                                continue
                        else:
                            continue

                        # Обрабатываем ответ пользователя на выданный профиль
                        for inner_event in vkinder_user.longpool.listen():
                            if inner_event.type == VkEventType.MESSAGE_NEW and inner_event.to_me:
                                inner_incoming_msg = inner_event.text.lower()

                                if inner_incoming_msg == 'в чс':

                                    request_status = session.query(Accounts).filter_by(status='favorites').all()
                                    for row in request_status:
                                        if user['id'] == row.vk_id:
                                            status_changer(session, row.vk_id, 'blacklist')
                                            vkinder_user.send_some_msg(vkinder_user_id, 'Статус изменён! '
                                                                                        'Человек добавлен в ЧС!')
                                            break
                                    else:
                                        account_for_db = Accounts(vk_id=user['id'],
                                                                  name=user['first_name'],
                                                                  surname=user['last_name'],
                                                                  age=datetime.date.today().year - int(
                                                                      user['bdate'].split('.')[-1]),
                                                                  gender_id=user['sex'],
                                                                  city_id=user['city']['id'],
                                                                  city_title=user['city']['title'],
                                                                  status='blacklist',
                                                                  profile_link=f'https://vk.com/id{user["id"]}',
                                                                  vkinder_user_id=vkinder_user_id)
                                        session.add(account_for_db)
                                        session.commit()
                                        vkinder_user.send_some_msg(vkinder_user_id, 'Человек добавлен в ЧС!')
                                        break
                                    break

                                elif inner_incoming_msg == 'в избранное':

                                    request_favorites = session.query(Accounts).filter_by(status='favorites').all()
                                    for row in request_favorites:
                                        if user['id'] == row.vk_id:
                                            favorites_list_flag = 1
                                            break
                                    if favorites_list_flag:
                                        vkinder_user.send_some_msg(vkinder_user_id, 'Найденный пользователь уже '
                                                                                    'в Избранном, продолжаем!')
                                        favorites_list_flag = 0
                                        break
                                    account_for_db = Accounts(vk_id=user['id'],
                                                              name=user['first_name'],
                                                              surname=user['last_name'],
                                                              age=datetime.date.today().year - int(
                                                                  user['bdate'].split('.')[-1]),
                                                              gender_id=user['sex'],
                                                              city_id=user['city']['id'],
                                                              city_title=user['city']['title'],
                                                              status='favorites',
                                                              profile_link=f'https://vk.com/id{user["id"]}',
                                                              vkinder_user_id=vkinder_user_id)
                                    session.add(account_for_db)
                                    for i in range(len(user_photos)):
                                        photos_for_db = Photos(vk_id=user['id'],
                                                               photo_attachment=f'photo{user["id"]}_{user_photos[i][0]}')
                                        session.add(photos_for_db)
                                    session.commit()
                                    vkinder_user.send_some_msg(vkinder_user_id, 'Человек добавлен в Избранное!')
                                    break

                                elif inner_incoming_msg == 'дальше':

                                    vkinder_user.send_some_msg(vkinder_user_id, 'Переходим в следующему человеку!')
                                    break

                                elif inner_incoming_msg == 'показать избранное':

                                    vkinder_user.send_some_msg(vkinder_user_id, 'Просмотр Избранного!')
                                    request = session.query(Accounts).filter_by(status='favorites').all()
                                    for row in request:
                                        vkinder_user.send_some_msg(vkinder_user_id,
                                                                   f'{row.name} {row.surname}, {row.age}, '
                                                                   f'{row.city_title}, {row.profile_link}')
                                    continue

                                else:

                                    vkinder_user.send_some_msg(vkinder_user_id, 'Неизвестная команда!')
                                    continue

                    # Когда найденные профили закончились уведомляем пользователя
                    # и возвращаем начальные настройки
                    vkinder_user.send_some_msg(vkinder_user_id, 'Пользователи закончились!')
                    welcome_msg_flag = 0
                    age_step = -3

                    continue

                else:
                    vkinder_user.send_some_msg(vkinder_user_id, 'Неизвестная команда!')


if __name__ == "__main__":
    main()
