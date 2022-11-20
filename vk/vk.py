import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import datetime
import time
from vk_api.keyboard import VkKeyboard, VkKeyboardColor


def preview_photos(user_photo_list: list) -> list:
    preview_photo_list = [
        {'photo_id': photo['id'], 'likes': photo['likes']['count'],
         'photo_link': [sizes['url'] for sizes in photo['sizes']][-1]}
        for photo in user_photo_list["items"]]
    preview_photo_list.sort(key=lambda dictionary: dictionary['likes'])
    link_list = [[link['photo_id'], link['likes'], link['photo_link']] for link in preview_photo_list[-3:]]
    return link_list

# def create_keyboard(msg):
#     keyboard = VkKeyboard(one_time=False)
#     if msg == "начать" or "id" or "profile" or "найди пару":
#         keyboard.add_button(label="id", color=VkKeyboardColor.POSITIVE)
#         keyboard.add_line()
#         keyboard.add_button(label="profile", color=VkKeyboardColor.PRIMARY)
#         keyboard.add_button(label="найди пару", color=VkKeyboardColor.PRIMARY)
#         keyboard = keyboard.get_keyboard()
#     else:
#         keyboard.add_button(label="начать", color=VkKeyboardColor.POSITIVE)
#         keyboard = keyboard.get_keyboard()
#     return keyboard


class VK:
    def __init__(self, user_token: str, group_token: str):
        self.user_token = user_token
        self.group_token = group_token
        self.group_session = vk_api.VkApi(token=self.group_token)
        self.user_session = vk_api.VkApi(token=self.user_token)
        self.group_session_api = self.group_session.get_api()
        self.user_session_api = self.user_session.get_api()
        self.longpool = VkLongPoll(self.group_session)

    def send_some_msg(self, vkinder_user_id: int, some_text: str, keyboard=None, attachment=None) -> None:
        self.group_session.method('messages.send', {'user_id': vkinder_user_id, 'message': some_text, 'random_id': 0,
                                                    'keyboard': keyboard, 'attachment': attachment})

    # def send_some_msg(self, vkinder_user_id, some_text, keyboard):
    #     self.group_session.method("messages.send", {"user_id": vkinder_user_id, "message": some_text,
    #                                                 "random_id": 0, "keyboard": keyboard})

    def profile_info(self, vkinder_user_id: int) -> dict:
        user = self.group_session.method('users.get', {'user_ids': vkinder_user_id,
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

    def user_search(self, count: str, city: str, vkinder_user_sex: str, vkinder_user_age: str, age_step: int) -> list:
        found_users = self.user_session_api.users.search(count=count,
                                                         sex='1' if vkinder_user_sex == '2' else '2',
                                                         city=city, age_from=str(int(vkinder_user_age) + age_step),
                                                         age_to=str(int(vkinder_user_age) + age_step),
                                                         has_photo='1', status='6',
                                                         fields="city, bdate, sex")
        return found_users

    def get_photo(self, found_user_id: int) -> list:
        photo_list = self.user_session_api.photos.get(owner_id=found_user_id, album_id="profile", extended=1)
        return photo_list

    # def main(self):
    #     for event in self.longpool.listen():
    #         if event.type == VkEventType.MESSAGE_NEW and event.to_me:
    #             msg = event.text.lower()
    #             id = event.user_id
    #             profile_list = self.profile_info(id)
    #             city, sex, age = profile_list["city"], profile_list["sex"], int(profile_list["bdate"].split('.')[-1])
    #             keyboard = self.create_keyboard(msg)
    #             if msg == "начать":
    #                 self.send_some_msg(id, "Привет, друг!\n"
    #                                        "Давай начнем поиск партнера для общения.\n\n"
    #                                        "Сейчас я соберу о тебе информацию, для лучшего поиска.", keyboard)
                    # if msg:
                    #     if len(age.split(".")) <3:
                    #         self.send_some_msg(id, "Пожалуйста, введи сколько тебе лет.")
                    #         age = msg
                    #     else:
                    #         year = datetime.datetime.today().year
                    #         age = year - int(age.split(".")[-1])
                    # if msg:
                    #     if city == '':
                    #         self.send_some_msg(id, "Пожалуйста, введи свой город.")
                    #         city = msg
                    # self.send_some_msg(id, "B так:\n"
                    #                        f"Вас зовут - {profile_list['name']}\n"
                    #                        f"Ваш возраст - {age} лет\n"
                    #                        f"ID вашего города - {city}")

                # elif msg == "id":
                #     self.send_some_msg(id, f'Твой ID - {id}', keyboard)
                #
                # elif msg == "найди пару":
                #     users = self.user_search(city, sex, age)['items']
                #     user_for_db = []
                #     for user in users:
                #         if user["is_closed"] is False and 'city' in user:
                #             photo_list = self.get_photo(user["id"])
                #             if photo_list["count"] > 2:
                #                 users_photo = preview_photos(photo_list)
                #                 self.send_some_msg(id, f'Имя - {user["first_name"]} {user["last_name"]}\n '
                #                                        f'Ссылка - https://vk.com/id{user["id"]}\n'
                #                                        f'Пол - {user["sex"]}\n'
                #                                        f'ID - {user["id"]}\n'
                #                                        f"Код города - {user['city']['id']}\n"
                #                                        f'Фото:\n{users_photo}', keyboard)
                #                 year = datetime.datetime.today().year
                #                 user_for_db.append({"vk_id": user["id"],
                #                                     "name": user["first_name"],
                #                                     "surname": user["last_name"],
                #                                     "age": year - int(user["bdate"].split(".")[-1]),
                #                                     "gender_id": user["sex"],
                #                                     "city_id": user['city']['id'],
                #                                     "profile_link": 'https://vk.com/id' + str(user["id"]),
                #                                     "photo_link": users_photo})
                #                 time.sleep(0.5)
                #                 print(user_for_db)
                #
                # elif msg == "profile":
                #     self.send_some_msg(id, f'Ваше имя - {profile_list["name"]}\n'
                #                            f'Пол - {"мужской" if profile_list["sex"] == 2 else "женский"}\n'
                #                            f'День рождения - {profile_list["bdate"]}\n'
                #                            f'Город - {profile_list["city"]}\n'
                #                            f'Семейное положение - {"Не женат" if profile_list["relation"] == 1 else "Встречаюсь" if profile_list["relation"] == 2 else "Помолвлен" if profile_list["relation"] == 3 else "Женат" if profile_list["relation"] == 4 else "Всё сложно" if profile_list["relation"] == 5 else "В активном поиске" if profile_list["relation"] == 6 else "Влюблен" if profile_list["relation"] == 7 else "В активном поиске" if profile_list["relation"] == 8 else "Не выбрано"}'
                #                        , keyboard)
                #
                # else:
                #     self.send_some_msg(id, "Прости, но я не знаю такой команды 😢", keyboard)
