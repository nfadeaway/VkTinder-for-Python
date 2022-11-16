import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType


vk_session = vk_api.VkApi(token="токен группы")
session_api = vk_session.get_api()
longpool = VkLongPoll(vk_session)

def send_some_msg(id, some_text):
    vk_session.method("messages.send", {"user_id":id, "message":some_text,"random_id":0})

for event in longpool.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            msg = event.text.lower()
            id = event.user_id
            if msg == "привет":
                send_some_msg(id, "Привет, друг!\nЯ имею следующие возможности:\n\nid - показать мой ID")
            elif msg == "id":
                send_some_msg(id, f'Твой ID - {id}')
            else:
                send_some_msg(id, "Прости, но я не знаю такой команды 😢")

