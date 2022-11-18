import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import datetime
import time
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

class VK:
    def __init__(self, user_token, group_token):
        self.user_token = user_token
        self.group_token = group_token

        self.group_session = vk_api.VkApi(token=self.group_token)
        self.session_api = self.group_session.get_api()
        self.longpool = VkLongPoll(self.group_session)

    def create_keyboard(self, msg):
        keyboard = VkKeyboard(one_time=False)
        if msg == "начать" or "id" or "profile" or "найди пару":
            keyboard.add_button(label="id", color=VkKeyboardColor.POSITIVE)
            keyboard.add_line()
            keyboard.add_button(label="profile", color=VkKeyboardColor.PRIMARY)
            keyboard.add_button(label="найди пару", color=VkKeyboardColor.PRIMARY)
            keyboard = keyboard.get_keyboard()
        else:
            keyboard.add_button(label="начать", color=VkKeyboardColor.POSITIVE)
            keyboard = keyboard.get_keyboard()
        return keyboard

    def send_some_msg(self, id, some_text, keyboard):
        self.group_session.method("messages.send", {"user_id":id, "message":some_text,"random_id":0, "keyboard": keyboard})

    def profile_info(self, id):
        user = self.group_session.method("users.get", {"user_ids":id, "fields": "sex, bdate, city, relation"})
        name = f'{user[0]["first_name"]} {user[0]["last_name"]}'
        sex = user[0]["sex"]
        bdate = user[0]["bdate"]
        relation = user[0]["relation"]
        city = user[0]["city"]['id'] if 'city' in user[0] else ''
        return {'name':name, 'sex': sex, 'bdate': bdate, 'relation':relation, 'city':city}

    def user_search(self, city, sex, age):
        vk = vk_api.VkApi(token=self.user_token)
        api = vk.get_api()
        year = datetime.datetime.today().year
        search = api.users.search(count=50,
                                  sex="1" if sex == 2 else "2",
                                  city=city, age_from=str(year-age-3),
                                  age_to=str(year - age + 2),
                                  has_photo=1,
                                  fields="city, bdate, sex")
        return search

    def get_photo(self, id):
        vk = vk_api.VkApi(token=self.user_token)
        api = vk.get_api()
        photo_list = api.photos.get(owner_id=id, album_id="profile", extended=1)
        return photo_list

    def preview_photo(self, photo_list):
        preview_photo = [{'likes': photo['likes']['count'], "photo_link": [sizes["url"] for sizes in photo["sizes"]][-1]}
                         for photo in photo_list["items"]]
        preview_photo.sort(key=lambda dictionary: dictionary['likes'])
        link_list = [link["photo_link"] for link in preview_photo[-3:]]
        return link_list

    def main(self):
        for event in self.longpool.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                msg = event.text.lower()
                id = event.user_id
                profile_list = self.profile_info(id)
                city, sex, age = profile_list["city"], profile_list["sex"], int(profile_list["bdate"].split('.')[-1])
                keyboard = self.create_keyboard(msg)
                if msg == "начать":
                    self.send_some_msg(id, "Привет, друг!\n"
                                      "Давай начнем поиск партнера для общения.\n\n"
                                           "Сейчас я соберу о тебе информацию, для лучшего поиска.", keyboard)
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

                elif msg == "id":
                    self.send_some_msg(id, f'Твой ID - {id}', keyboard)

                elif msg == "найди пару":
                    users = self.user_search(city, sex, age)['items']
                    user_for_db = []
                    for user in users:
                        if user["is_closed"] is False and 'city' in user:
                            photo_list = self.get_photo(user["id"])
                            if photo_list["count"] > 2:
                                users_photo = self.preview_photo(photo_list)
                                self.send_some_msg(id, f'Имя - {user["first_name"]} {user["last_name"]}\n '
                                                       f'Ссылка - https://vk.com/id{user["id"]}\n'
                                                       f'Пол - {user["sex"]}\n'
                                                       f'ID - {user["id"]}\n'
                                                       f"Код города - {user['city']['id']}\n"
                                                       f'Фото:\n{users_photo}', keyboard)
                                year = datetime.datetime.today().year
                                user_for_db.append({"vk_id": user["id"],
                                               "name": user["first_name"],
                                               "surname": user["last_name"],
                                               "age": year - int(user["bdate"].split(".")[-1]),
                                               "gender_id":user["sex"],
                                               "city_id": user['city']['id'],
                                               "profile_link": 'https://vk.com/id'+str(user["id"]),
                                               "photo_link": users_photo})
                                time.sleep(0.5)
                                print(user_for_db)

                elif msg == "profile":
                    self.send_some_msg(id, f'Ваше имя - {profile_list["name"]}\n'
                                      f'Пол - {"мужской" if profile_list["sex"]==2 else "женский"}\n'
                                      f'День рождения - {profile_list["bdate"]}\n'
                                      f'Город - {profile_list["city"]}\n'
                                      f'Семейное положение - {"Не женат" if profile_list["relation"]==1 else "Встречаюсь" if profile_list["relation"]==2 else "Помолвлен" if profile_list["relation"]==3 else "Женат" if profile_list["relation"]==4 else "Всё сложно" if profile_list["relation"]==5 else "В активном поиске" if profile_list["relation"]==6 else "Влюблен" if profile_list["relation"]==7 else "В активном поиске" if profile_list["relation"]==8 else "Не выбрано"}'
                    , keyboard)

                else:
                    self.send_some_msg(id, "Прости, но я не знаю такой команды 😢", keyboard)