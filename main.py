import time

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from pprint import pprint
import datetime


user_token = "vk1.a.jRn_RRJV-FjTvWbt8cRNjTLw14EqOzk77rLuYuLIdHBYdyWj4Mi1GsXk_Sj8-WDD8YztyaEHEsLt8spT_VcG7q45GERAoWv7qD_YxpTfjdGKW4yRXgwk8ajpOysQ6c_Ov7__xpshmIv4FLAzlcOqY652aytGiU0XSMPUEbIxNe5BPhoA0kI-zs_5M_ZUOwZs"
group_token = "vk1.a.tuocZ2TPyOLkMOvKD_Ml2CKIomMLyHrUMo8v2QfG6c2PBsJPRbo-R9-uMugnReaSIKjM706ghxhXh_dmJd0O52cd1LY2gShiE9gcKdw8eMdMroIRO2tnA41S6mgXOW6o3H6o3bkux_YLEdtrS7Ch-FYQ1vTKftPPW5b5ZpiCU3CdQ5WChMzKrf3ZsFwQN1vrm36Q-Bh301lH_zlw6TbisA"
group_session = vk_api.VkApi(token=group_token)
session_api = group_session.get_api()
longpool = VkLongPoll(group_session)

def send_some_msg(id, some_text):
    group_session.method("messages.send", {"user_id":id, "message":some_text,"random_id":0})

def profile_info(id):
    user = group_session.method("users.get", {"user_ids":id, "fields": "sex, bdate, city, relation"})
    name = f'{user[0]["first_name"]} {user[0]["last_name"]}'
    sex = user[0]["sex"]
    bdate = user[0]["bdate"]
    relation = user[0]["relation"]
    city = user[0]["city"]['id']
    return {'name':name, 'sex': sex, 'bdate': bdate, 'relation':relation, 'city':city}

def user_search(city, sex, age):
    vk = vk_api.VkApi(token=user_token)
    api = vk.get_api()
    year = datetime.datetime.today().year
    search = api.users.search(count=20,
                              sex="1" if sex == 2 else "2",
                              city=city, age_from=str(year-age-3),
                              age_to=str(year - age + 2),
                              has_photo=1,
                              fields="city, photo_max")
    return search
def get_photo(id):
    vk = vk_api.VkApi(token=user_token)
    api = vk.get_api()
    photo_list = api.photos.get(owner_id=id, album_id="profile", extended=1)
    return photo_list

def preview_photo(photo_list):
    preview_photo = [{'likes': photo['likes']['count'], "photo_link": [sizes["url"] for sizes in photo["sizes"]][-1]}
                     for photo in photo_list["items"]]
    preview_photo.sort(key=lambda dictionary: dictionary['likes'])
    link_list = [link["photo_link"] for link in preview_photo[-3:]]
    return link_list



for event in longpool.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            msg = event.text.lower()
            id = event.user_id
            profile_list = profile_info(id)
            city, sex, age = str(profile_list["city"]), profile_list["sex"], int(profile_list["bdate"].split('.')[2])



            if msg == "привет":
                send_some_msg(id, "Привет, друг!\n"
                                  "Я имею следующие возможности:\n\n"
                                  "id - показать мой ID\nprofile - показать мои данные")
            elif msg == "id":
                send_some_msg(id, f'Твой ID - {id}')


            elif msg == "0":
                users = user_search(city, sex, age)['items']
                user_dict = [{"name": user['first_name'] + " " + user['last_name'], 'id': user['id']} for user in users
                             if user['is_closed'] == False]
                for user in user_dict:
                    photo_list = get_photo(user["id"])
                    if photo_list["count"] > 2:
                        send_some_msg(id, f'Имя - {user["name"]}\n Ссылка - https://vk.com/id{user["id"]}\n'
                                          f'Фото:\n{preview_photo(photo_list)}')
                        time.sleep(0.5)


            elif msg == "profile":
                send_some_msg(id, f'Ваше имя - {profile_list["name"]}\n'
                                  f'Пол - {"мужской" if profile_list["sex"]==2 else "женский"}\n'
                                  f'День рождения - {profile_list["bdate"]}\n'
                                  f'Город - {profile_list["city"]}\n'
                                  f'Семейное положение - {"Не женат" if profile_list["relation"]==1 else "Встречаюсь" if profile_list["relation"]==2 else "Помолвлен" if profile_list["relation"]==3 else "Женат" if profile_list["relation"]==4 else "Всё сложно" if profile_list["relation"]==5 else "В активном поиске" if profile_list["relation"]==6 else "Влюблен" if profile_list["relation"]==7 else "В активном поиске" if profile_list["relation"]==8 else "Не выбрано"}'
                )


            else:
                send_some_msg(id, "Прости, но я не знаю такой команды 😢")

