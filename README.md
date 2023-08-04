# О проекте
![Static Badge](https://img.shields.io/badge/python%20-%20black?logo=python&logoColor=%23FFDE56)
![Static Badge](https://img.shields.io/badge/postgresql%20-%20black?logo=postgresql)

[Командный проект по курсу "Профессиональная работа с Python"](https://github.com/netology-code/adpy-team-diplom/tree/main)

VK-бот для поиска пары пользователю на основе его возраста, пола и места проживания с возможностью добавлять найденные анкеты в "Избранное" и в "ЧС".

## Дополнительная информация
Для работы программы необходимо получить:
- [персональный токен VK](https://dev.vk.com/api/access-token/getting-started)
- [токен сообщества VK](https://dev.vk.com/api/access-token/getting-started)

## Настройки программы
- В программе используется СУБД PostgreSQL
- Библиотека [`DotEnv`](https://habr.com/ru/post/472674/) для получения переменных из окружения

Для работы программы в корне вашего проекта необходимо создать файл окружения `.env` формата:
```
USER_TOKEN='Персональный токен' 
GROUP_TOKEN='Токен собобщества' 
GROUP_ID='ID вашего сообщества' 
DSN='postgresql://NAME:PASSWORD@localhost:PORT/DatabaseName'
```
## Запись работы программы
![Работа программы](/gif/vkinder.gif)