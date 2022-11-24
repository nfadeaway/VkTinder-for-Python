from dotenv import load_dotenv
import os
from vk_api.bot_longpoll import VkBotEventType
from vk.vk import VK
from threading import Thread
from database.database import User, Preferences
import sqlalchemy as sq
from sqlalchemy.orm import sessionmaker

load_dotenv()

user_dict = {}
vk = VK()


def listener(self_id, session):
    user = session.query(User).filter_by(vk_id=self_id).all()
    if user:
        pass
    else:
        session.add(User(vk_id=self_id))
        session.commit()

    vkinder_user_info = vk.profile_info(self_id)
    vkinder_user_city = vkinder_user_info['city']
    vkinder_user_sex = vkinder_user_info['sex']
    vkinder_user_age = vkinder_user_info['age']

    regular_keyboard = vk.keyboard()[1]
    welcome_keyboard = vk.keyboard()[0]

    if vkinder_user_age == '':
        vk.send_message(vk.vk_group_session, self_id,
                        "Не могу понять, сколько тебе лет, напиши для более точного подбора.")
        for event in vk.longpoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                if self_id == event.obj.message["from_id"]:
                    if event.obj.message["text"].isdigit() and int(event.obj.message["text"]) > 0 and int(
                            event.obj.message["text"]) < 100:
                        vkinder_user_age = int(event.obj.message["text"])
                        break
                    else:
                        vk.send_message(vk.vk_group_session, self_id,
                                        "Пока не введёшь нормальный возраст, ничего не получится.")

    count = 100
    age_step = 3
    found_user = vk.vk_user.users.search(count=count, sex='1' if vkinder_user_sex == '2' else '2',
                                         city=vkinder_user_city, age_from=str(int(vkinder_user_age) + age_step),
                                         age_to=str(int(vkinder_user_age) + age_step), has_photo='1',
                                         status='6', fields="city, bdate, sex")

    # black_list = []
    #
    # request_blacklist = session.query(Preferences).filter_by(vk_id=self_id, status_id=2).all()
    #
    # for raw in request_blacklist:
    #     black_list.append(raw.watched_vk_id)

    for user in found_user['items']:

        if user_dict[self_id] == 1:
            vk.send_message(vk.vk_group_session, self_id, text="Для начала работы нажмите начать.",
                            keyboard=welcome_keyboard.get_keyboard())
            break

        request_preferences = session.query(Preferences).filter_by(vk_id=self_id, watched_vk_id=user["id"]).all()

        if request_preferences:
            vk.send_message(vk.vk_group_session, self_id, "попался аккаунт из списка предпочтений, ищем дальше...")
            continue

        # if user["id"] in black_list:
        #     vk.send_message(vk.vk_group_session, self_id, "попался аккаунт из черного списка, ищем дальше...")
        #     continue

        if user['is_closed']:
            vk.send_message(vk.vk_group_session, self_id, "попался закрытый аккаунт, ищем дальше...")
            continue

        user_photo_list = vk.vk_user.photos.get(owner_id=user["id"], album_id="profile", extended=1)
        if user_photo_list['count'] > 2:
            user_photos = vk.preview_photos(user_photo_list)
            vk.send_message(vk.vk_group_session, self_id, f'{user["first_name"]} {user["last_name"]}\n'
                                                          f'https://vk.com/id{user["id"]}\n',
                            f'photo{user["id"]}_{user_photos[0][0]},'
                            f'photo{user["id"]}_{user_photos[1][0]},'
                            f'photo{user["id"]}_{user_photos[2][0]}', keyboard=regular_keyboard.get_keyboard())
        else:
            vk.send_message(vk.vk_group_session, self_id, "у пользователя недостаточно фото, ищем дальше...")
            continue

        for event in vk.longpoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                if self_id == event.obj.message["from_id"]:
                    if event.obj.message["text"].lower() == "дальше":
                        vk.send_message(vk.vk_group_session, event.obj.message["from_id"], text="ожидай...",
                                        keyboard=regular_keyboard.get_keyboard())
                        break

                    if event.obj.message["text"].lower() == "в избранное":
                        session.add(Preferences(vk_id=self_id, watched_vk_id=user["id"], status_id=1))
                        session.commit()
                        vk.send_message(vk.vk_group_session, event.obj.message["from_id"],
                                        text="добавили в избранное, ищем дальше...",
                                        keyboard=regular_keyboard.get_keyboard())
                        break

                    if event.obj.message["text"].lower() == "в чс":
                        session.add(Preferences(vk_id=self_id, watched_vk_id=user["id"], status_id=2))
                        session.commit()
                        vk.send_message(vk.vk_group_session, event.obj.message["from_id"],
                                        text="добавили в ЧС, ищем дальше...",
                                        keyboard=regular_keyboard.get_keyboard())
                        # black_list.append(user["id"])
                        break

                    if event.obj.message["text"].lower() == "моё избранное":
                        request_favorite_list = session.query(Preferences).filter_by(vk_id=self_id, status_id=1).all()
                        for user in request_favorite_list:
                            data = vk.vk_user.users.get(user_id=user.watched_vk_id, fields="first_name, last_name")
                            first_name = data[0]['first_name']
                            last_name = data[0]['last_name']
                            user_photo_list = vk.vk_user.photos.get(owner_id=user.watched_vk_id, album_id="profile",
                                                                    extended=1)
                            user_photos = vk.preview_photos(user_photo_list)
                            vk.send_message(vk.vk_group_session, self_id, f'{first_name} {last_name}\n'
                                                                          f'https://vk.com/id{user.watched_vk_id}\n',
                                            f'photo{user.watched_vk_id}_{user_photos[0][0]},'
                                            f'photo{user.watched_vk_id}_{user_photos[1][0]},'
                                            f'photo{user.watched_vk_id}_{user_photos[2][0]}',
                                            keyboard=regular_keyboard.get_keyboard())
                        continue

                    elif event.obj.message["text"] == "выход":
                        vk.send_message(vk.vk_group_session, event.obj.message["from_id"], text="выходим")
                        user_dict[event.obj.message["from_id"]] = 1
                        break


def main():
    engine = sq.create_engine(os.getenv('DSN'))

    Session = sessionmaker(bind=engine)
    session = Session()

    welcome_keyboard = vk.keyboard()[0]

    for event in vk.longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:

            if event.obj.message["from_id"] not in user_dict:
                vk.send_message(vk.vk_group_session, event.obj.message["from_id"],
                                text="Для начала работы нажмите начать.",
                                keyboard=welcome_keyboard.get_keyboard())
                user_dict[event.obj.message["from_id"]] = 1

            if event.obj.message["text"].lower() == "мои данные" and user_dict[event.obj.message["from_id"]] == 1:
                self_id = event.obj.message["from_id"]
                vk.send_message(vk.vk_group_session, event.obj.message["from_id"], text=self_id,
                                keyboard=welcome_keyboard.get_keyboard())

            elif event.obj.message["text"].lower() == "начать" and user_dict[event.obj.message["from_id"]] == 1:
                self_id = event.obj.message["from_id"]
                vk.send_message(vk.vk_group_session, event.obj.message["from_id"], text="вошли в поиск")
                user_dict[event.obj.message["from_id"]] = 2
                inner_listen = Thread(target=listener, args=(self_id, session))
                inner_listen.start()

            # else:
            #     if user_dict[event.obj.message["from_id"]] == 1:
            #         send_message(vk_group_session, event.obj.message["from_id"], text="неизвестно")


if __name__ == "__main__":
    main()
