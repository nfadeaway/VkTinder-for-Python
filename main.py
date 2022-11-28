from vk_api.bot_longpoll import VkBotEventType
from database.db import DB
from vk.vk import VK
from threading import Thread
import random


user_dict = {}
vk = VK()
db = DB()


def listener(self_id, session):
    db.check_user(self_id)

    vkinder_user_info = vk.profile_info(self_id)
    vkinder_user_city = vkinder_user_info['city']
    vkinder_user_sex = vkinder_user_info['sex']
    vkinder_user_age = vkinder_user_info['age']
    back_keyboard = vk.keyboard()[2]
    regular_keyboard = vk.keyboard()[1]
    welcome_keyboard = vk.keyboard()[0]

    if vkinder_user_age == '':
        vk.send_message(vk.vk_group_session, self_id,
                        "Не могу понять, сколько тебе лет, напиши для более точного подбора.")
        for event in vk.longpoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                if self_id == event.obj.message["from_id"]:
                    if event.obj.message["text"].isdigit() and int(event.obj.message["text"]) > 17 and int(
                            event.obj.message["text"]) < 101:
                        vkinder_user_age = int(event.obj.message["text"])
                        break
                    else:
                        vk.send_message(vk.vk_group_session, self_id,
                                        "Пока не введёшь нормальный возраст, ничего не получится. (доступный диапазон "
                                        "18-100)")

    count = 100
    user_list = vk.search(vkinder_user_sex, vkinder_user_city, vkinder_user_age, count)

    if not user_list:
        vk.send_message(vk.vk_group_session, self_id, "Тебе пары не нашлось, попробуй скорректировать свои "
                                                      "данные.\nМожет ты не указал свой город в личном профиле?",
                        keyboard=welcome_keyboard.get_keyboard())
        user_dict[self_id] = 1
        return

    random.shuffle(user_list)

    user_list_len = len(user_list) + 1

    for user in user_list:

        user_list_len -= 1

        if user_list_len == 1:
            vk.send_message(vk.vk_group_session, self_id,
                            text="Это был последний кандидат в подборе, можем начать заново.",
                            keyboard=welcome_keyboard.get_keyboard())
            user_dict[self_id] = 1
            break

        if user_dict[self_id] == 1:
            vk.send_message(vk.vk_group_session, self_id, text="Для начала работы нажмите начать.",
                            keyboard=welcome_keyboard.get_keyboard())
            break

        if db.request_preferences(self_id, user["id"]):
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
            continue

        for event in vk.longpoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                if self_id == event.obj.message["from_id"]:
                    if event.obj.message["text"].lower() == "дальше":
                        break

                    if event.obj.message["text"].lower() == "в избранное":
                        db.add_favorite(self_id, user["id"])
                        vk.send_message(vk.vk_group_session, event.obj.message["from_id"],
                                        text=f"{user['first_name']} {user['last_name']} добавлен(-а) в избранное.",
                                        keyboard=regular_keyboard.get_keyboard())
                        break

                    if event.obj.message["text"].lower() == "в чс":
                        db.add_blacklist(self_id, user["id"])
                        vk.send_message(vk.vk_group_session, event.obj.message["from_id"],
                                        text=f"{user['first_name']} {user['last_name']} добавлен(-а) в ЧС.",
                                        keyboard=regular_keyboard.get_keyboard())
                        break

                    if event.obj.message["text"].lower() == "моё избранное":
                        request_favorite_list = db.request_favorite_list(self_id)
                        for favorite_user in request_favorite_list:
                            data = vk.vk_user.users.get(user_id=favorite_user.watched_vk_id, fields="first_name, last_name")
                            first_name = data[0]['first_name']
                            last_name = data[0]['last_name']
                            user_photo_list = vk.vk_user.photos.get(owner_id=favorite_user.watched_vk_id, album_id="profile",
                                                                    extended=1)
                            user_photos = vk.preview_photos(user_photo_list)
                            vk.send_message(vk.vk_group_session, self_id, f'{first_name} {last_name}\n'
                                                                          f'https://vk.com/id{favorite_user.watched_vk_id}\n',
                                            f'photo{favorite_user.watched_vk_id}_{user_photos[0][0]},'
                                            f'photo{favorite_user.watched_vk_id}_{user_photos[1][0]},'
                                            f'photo{favorite_user.watched_vk_id}_{user_photos[2][0]}',
                                            keyboard=back_keyboard.get_keyboard())
                        continue

                    elif event.obj.message["text"] == "выход":
                        vk.send_message(vk.vk_group_session, event.obj.message["from_id"], text="выходим")
                        user_dict[event.obj.message["from_id"]] = 1
                        break


def main():
    # Блок создания таблиц (необходим лишь для первого запуска)
    db.drop_tables()
    db.create_tables()
    db.status_filler()
    # ---------------------------------------------------------
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
                vk.send_message(vk.vk_group_session, event.obj.message["from_id"], text="Начинаем поиск")
                user_dict[event.obj.message["from_id"]] = 2
                inner_listen = Thread(target=listener, args=(self_id, db.session))
                inner_listen.start()


if __name__ == "__main__":
    main()
