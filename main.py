from dotenv import load_dotenv
import os
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from threading import Thread
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import datetime
from database.database import Status, User, Preferences, drop_tables, create_tables, status_filler
import sqlalchemy as sq
from sqlalchemy.orm import sessionmaker

user_dict = {}

load_dotenv()

vk_group_session = vk_api.VkApi(token=os.getenv('GROUP_TOKEN'))
vk_user_session = vk_api.VkApi(token=os.getenv('USER_TOKEN'))
vk_group = vk_group_session.get_api()
vk_user = vk_user_session.get_api()
longpoll = VkBotLongPoll(vk_group_session, group_id=os.getenv('GROUP_ID'))

welcome_keyboard = VkKeyboard(one_time=True)
regular_keyboard = VkKeyboard()
welcome_keyboard.add_button(label="Начать", color=VkKeyboardColor.POSITIVE)
welcome_keyboard.add_button(label="Мои данные", color=VkKeyboardColor.POSITIVE)
regular_keyboard.add_button(label="Дальше", color=VkKeyboardColor.POSITIVE)
regular_keyboard.add_button(label="В избранное", color=VkKeyboardColor.POSITIVE)
regular_keyboard.add_button(label="В ЧС", color=VkKeyboardColor.NEGATIVE)
regular_keyboard.add_line()
regular_keyboard.add_button(label="Моё избранное", color=VkKeyboardColor.SECONDARY)


def preview_photos(user_photo_list: list) -> list:
    preview_photo_list = [
        {'photo_id': photo['id'], 'likes': photo['likes']['count'],
         'photo_link': [sizes['url'] for sizes in photo['sizes']][-1]}
        for photo in user_photo_list["items"]]
    preview_photo_list.sort(key=lambda dictionary: dictionary['likes'])
    link_list = [[link['photo_id'], link['likes'], link['photo_link']] for link in preview_photo_list[-3:]]
    return link_list


def get_photo(found_user_id: int) -> list:
    photo_list = vk_user.photos.get(owner_id=found_user_id, album_id="profile", extended=1)
    return photo_list


def send_message(session, vk_id: int, text: str, attachment=None, keyboard=None) -> None:
    session.method('messages.send',
                   {'user_id': vk_id, 'message': text, 'random_id': 0, 'keyboard': keyboard, 'attachment': attachment})


def profile_info(vkinder_user_id: int) -> dict:
    user = vk_group_session.method('users.get', {'user_ids': vkinder_user_id,
                                                 'fields': 'sex, bdate, city, relation'})
    name = f'{user[0]["first_name"]} {user[0]["last_name"]}'
    sex = user[0]['sex']
    if 'bdate' in user[0]:
        if len(user[0]['bdate'].split('.')) == 3:
            age = datetime.date.today().year - int(user[0]['bdate'].split('.')[-1])
        else:
            age = ''
    else:
        age = ''
    relation = user[0]['relation']
    city = user[0]['city']['id'] if 'city' in user[0] else ''
    city_title = user[0]['city']['title'] if 'city' in user[0] else ''
    return {'name': name, 'sex': str(sex), 'age': str(age), 'relation': str(relation), 'city': str(city),
            'city_title': city_title}


def listener(self_id, session):
    session.add(User(vk_id=self_id))
    session.commit()

    vkinder_user_info = profile_info(self_id)
    vkinder_user_name = vkinder_user_info['name']
    vkinder_user_city = vkinder_user_info['city']
    vkinder_user_city_title = vkinder_user_info['city_title']
    vkinder_user_sex = vkinder_user_info['sex']
    vkinder_user_age = vkinder_user_info['age']

    if vkinder_user_age == '':
        send_message(vk_group_session, self_id, "Не могу понять, сколько тебе лет, напиши для более точного подбора.")
        for event in longpoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                if self_id == event.obj.message["from_id"]:
                    if event.obj.message["text"].isdigit() and int(event.obj.message["text"]) > 0 and int(
                            event.obj.message["text"]) < 100:
                        vkinder_user_age = int(event.obj.message["text"])
                        break
                    else:
                        send_message(vk_group_session, self_id,
                                     "Пока не введёшь нормальный возраст, ничего не получится.")

    count = 100
    age_step = 3
    found_user = vk_user.users.search(count=count, sex='1' if vkinder_user_sex == '2' else '2',
                                      city=vkinder_user_city, age_from=str(int(vkinder_user_age) + age_step),
                                      age_to=str(int(vkinder_user_age) + age_step), has_photo='1',
                                      status='6', fields="city, bdate, sex")

    black_list = []

    request_blacklist = session.query(Preferences).filter_by(vk_id=self_id, status_id=2).all()

    for raw in request_blacklist:
        black_list.append(raw.watched_vk_id)

    for user in found_user['items']:
        if user_dict[self_id] == 1:
            send_message(vk_group_session, self_id, text="Для начала работы нажмите начать.",
                         keyboard=welcome_keyboard.get_keyboard())
            break

        if user["id"] in black_list:
            send_message(vk_group_session, self_id, "попался аккаунт из черного списка, ищем дальше...")
            continue

        if user['is_closed']:
            send_message(vk_group_session, self_id, "попался закрытый аккаунт, ищем дальше...")
            continue

        user_photo_list = vk_user.photos.get(owner_id=user["id"], album_id="profile", extended=1)
        if user_photo_list['count'] > 2:
            user_photos = preview_photos(user_photo_list)
            send_message(vk_group_session, self_id, f'{user["first_name"]} {user["last_name"]}\n'
                                                    f'https://vk.com/id{user["id"]}\n',
                         f'photo{user["id"]}_{user_photos[0][0]},'
                         f'photo{user["id"]}_{user_photos[1][0]},'
                         f'photo{user["id"]}_{user_photos[2][0]}', keyboard=regular_keyboard.get_keyboard())
        else:
            send_message(vk_group_session, self_id, "у пользователя недостаточно фото, ищем дальше...")
            continue

        for event in longpoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                if self_id == event.obj.message["from_id"]:
                    if event.obj.message["text"].lower() == "дальше":
                        send_message(vk_group_session, event.obj.message["from_id"], text="ожидай...",
                                     keyboard=regular_keyboard.get_keyboard())
                        break

                    if event.obj.message["text"].lower() == "в избранное":
                        session.add(Preferences(vk_id=self_id, watched_vk_id=user["id"], status_id=1))
                        session.commit()
                        send_message(vk_group_session, event.obj.message["from_id"],
                                     text="добавили в избранное, ищем дальше...",
                                     keyboard=regular_keyboard.get_keyboard())
                        break

                    if event.obj.message["text"].lower() == "в чс":
                        session.add(Preferences(vk_id=self_id, watched_vk_id=user["id"], status_id=2))
                        session.commit()
                        send_message(vk_group_session, event.obj.message["from_id"],
                                     text="добавили в ЧС, ищем дальше...",
                                     keyboard=regular_keyboard.get_keyboard())
                        black_list.append(user["id"])
                        break

                    if event.obj.message["text"].lower() == "моё избранное":
                        request_favorite_list = session.query(Preferences).filter_by(vk_id=self_id, status_id=1).all()
                        for user in request_favorite_list:
                            data = vk_user.users.get(user_id=user.watched_vk_id, fields="first_name, last_name")
                            first_name = data[0]['first_name']
                            last_name = data[0]['last_name']
                            user_photo_list = vk_user.photos.get(owner_id=user.watched_vk_id, album_id="profile",
                                                                 extended=1)
                            user_photos = preview_photos(user_photo_list)
                            send_message(vk_group_session, self_id, f'{first_name} {last_name}\n'
                                                                    f'https://vk.com/id{user.watched_vk_id}\n',
                                         f'photo{user.watched_vk_id}_{user_photos[0][0]},'
                                         f'photo{user.watched_vk_id}_{user_photos[1][0]},'
                                         f'photo{user.watched_vk_id}_{user_photos[2][0]}',
                                         keyboard=regular_keyboard.get_keyboard())
                        continue

                    elif event.obj.message["text"] == "выход":
                        send_message(vk_group_session, event.obj.message["from_id"], text="выходим")
                        user_dict[event.obj.message["from_id"]] = 1
                        break


def main():
    engine = sq.create_engine(os.getenv('DSN'))
    drop_tables(engine)
    create_tables(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    status_filler(session)

    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:

            if event.obj.message["from_id"] not in user_dict:
                send_message(vk_group_session, event.obj.message["from_id"], text="Для начала работы нажмите начать.",
                             keyboard=welcome_keyboard.get_keyboard())
                user_dict[event.obj.message["from_id"]] = 1

            if event.obj.message["text"].lower() == "мои данные" and user_dict[event.obj.message["from_id"]] == 1:
                self_id = event.obj.message["from_id"]
                send_message(vk_group_session, event.obj.message["from_id"], text=self_id,
                             keyboard=welcome_keyboard.get_keyboard())

            elif event.obj.message["text"].lower() == "начать" and user_dict[event.obj.message["from_id"]] == 1:
                self_id = event.obj.message["from_id"]
                send_message(vk_group_session, event.obj.message["from_id"], text="вошли в поиск")
                user_dict[event.obj.message["from_id"]] = 2
                inner_listen = Thread(target=listener, args=(self_id, session))
                inner_listen.start()

            # else:
            #     if user_dict[event.obj.message["from_id"]] == 1:
            #         send_message(vk_group_session, event.obj.message["from_id"], text="неизвестно")


if __name__ == "__main__":
    main()