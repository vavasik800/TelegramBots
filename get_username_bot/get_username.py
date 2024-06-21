import os
import random
from asyncio import sleep
from typing import Optional, List, Dict
import re

from pyrogram import Client, types, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import InputPhoneContact, User
from loguru import logger

import config
from query_for_usernamebot import *
from dbEditor import SqlLiteEditor


class GetUsernameBot:
    """
    Класс, описывающий работу ЮзерБота для получения username telegram по номеру телефона.
    Работает с использованием telegram-api.
    Пример создания экземпляра:
        > client = GetUsernameBot(api_id, api_hash, is_bot)
    """
    __result: Optional[Dict[str, str]] = None  # переменная для резхультата вызова

    def __init__(self, api_id: Optional[str] = None, api_hash: Optional[str] = None, is_bot: bool=True) -> None:
        """
        Инициализация объекта класса для управления ЮзерБотом.
        :param api_id: инициализирующий параметр для работы телеграмм api
        :param api_hash: инициализирующий параметр для работы телеграмм api
        :param is_bot: bool-переменная для понимания класс, работает как бот или для получения телефона.
                       - False: снижает нагрузку на производительность,
                                не создает файл базы данных и не создает слушателей для методов телеграмм.
                       - True: создает базу для учета допущенных пользователей,
                               создает handlers для каждого из допущенных пользователей
        """
        logger.add('logs/debug.log',
                   format="{time}| {level}| {message}",
                   level="DEBUG",
                   rotation='10 MB',
                   compression='zip')
        self.api_id: Optional[str] = api_id
        self.api_hash: Optional[str] = api_hash
        self.is_bot = is_bot
        if self.api_id is None or self.api_id is None:
            # Если не переданны api_hash или api_id, то ошибка
            logger.error("Проверьте параметры api_hash, api_id.")
            raise ValueError

        try:
            self.app = Client('getUsernameFred', api_id=self.api_id, api_hash=api_hash)
        except Exception as error:
            logger.error("Не удалось установить соединение с клиентом телеграмм:")
            logger.error(error)
            return

        if self.is_bot:
            self.db_name = 'database_usernames.db'  # база данных для сохранения доступных пользователей
            create_db = os.path.isfile(self.db_name)
            try:
                self.db = SqlLiteEditor(self.db_name)  # Подключение к базе данных
            except Exception as error:
                logger.error("Не удалось установить подлкючение к базе:")
                logger.error(error)
                return
            if not create_db:
                # создание таблицы для юзеров
                self.db.run(CREATE_TABLE, 'create')
                logger.debug("Создана таблица для хранения допустимых пользователей.")

            self.good_id_users: Optional[List[int]] = None  # список ботов
            self.my_id = int(config.MY_ID)  # id для работы с каналами
            # self.__admin_message_handler = MessageHandler(self.listener_get_phone, filters=filters.chat(self.my_id))
            self.__admin_message_handler = MessageHandler(self.listener_get_phone, filters=filters.chat(self.my_id))
            self.dict_ids = {self.my_id: self.__admin_message_handler}
            if create_db:
                # если база данных была уже, то перебор всех пользоателей и создание слушателей
                users_ids = self.db.run(SELECT_IDS, 'select')
                for user in users_ids:
                    id_int = int(user['id_user'])
                    # создание слушателей
                    # admin_message_handler_new = MessageHandler(self.listener_get_phone, filters=filters.chat(id_int))
                    admin_message_handler_new = MessageHandler(self.listener_get_phone, filters=filters.chat(id_int))
                    self.dict_ids[id_int] = admin_message_handler_new
                    self.app.add_handler(self.dict_ids[id_int])
                    logger.debug(f"Добавлено прослушивание пользователя с id: {id_int}")
            self.app.add_handler(self.dict_ids[self.my_id])
            logger.debug(f"Добавлено прослушивание пользователя с id: {self.my_id}")
        logger.debug(f"Создан экземпляр класса.")
        return

    @property
    def result(self):
        return self.__result

    async def get_info_user(self, phone: str) -> Optional[User]:
        """
        Метод для получения информации о пользователе по номеру телефона.
        :param phone: номер телефона в виде строки.
        :return: словарь с данными пользователя, если не удается найти пользователя по номеру, то {}.
        """
        input_phone_contact = InputPhoneContact(phone, "getUsername")
        result = await self.app.import_contacts([input_phone_contact])
        if not result.users:
            return None
        if len(result.users) > 1:
            logger.warning(f"Количество результатов по номеру {phone}: {len(result.users)}")
            logger.warning(result.users)
        return result.users[0]

    def __set_user_id(self, message_text: str, type_fun='phone') -> int:
        """
        Метод для команды :setuser:, устанавливает пользователя, кто может отправлять боту запросы
        :param message_text: текст сообщения для разбора
        :param type_fun: тип функции, из которой вызов
        :return: 2 - пользователь успешно сохранен, 1 - неверная команда, 0 - сообщение не содержит команды
        """
        if message_text[0] == ':' and message_text[1:8] == 'setuser':
            # установка пользователей
            id_user_str = message_text.split(':')[-1].strip()
            user_id = int(id_user_str) if id_user_str.isnumeric() else None
            if user_id is None:
                return 1
            admin_message_handler_new = None
            if type_fun == 'phone':
                admin_message_handler_new = MessageHandler(self.listener_get_phone, filters=filters.chat(user_id))
            elif type_fun == 'phones':
                admin_message_handler_new = MessageHandler(self.listener_get_phones, filters=filters.chat(user_id))
            self.dict_ids[user_id] = admin_message_handler_new
            self.app.add_handler(self.dict_ids[user_id])
            self.db.run(INSERT_ID.format(id_user=user_id), 'insert')
            return 2
        return 0

    async def listener_get_phones(self, client: Client, message: types.Message) -> None:
        """
        Метод для обработки сообщения с множеством телефонных номеров и отправки только usernames.
        :param client: клиент
        :param message: сообщение
        :return: none
        """
        text_command = message.text
        is_setuser = self.__set_user_id(text_command, type_fun='phones')
        if is_setuser == 2:
            await self.app.send_message(message.chat.id, 'Пользователь установлен.')
            return
        elif is_setuser == 1:
            await self.app.send_message(message.chat.id, 'Неверная команда. Пример: ":setuser: 1234567"')
            return
        print(message.text)
        text = re.sub("[-()+ ]", "", message.text)
        print(text)
        list_phones = text.split('\n')
        print(list_phones)
        await self.app.send_message(message.chat.id, 'Идёт обработка результатов, подождите...')
        result_usernames = []
        for phone in list_phones:
            result = await self.get_info_user(phone)
            if result is None:
                result_usernames.append('-')
                continue
            result_usernames.append(str(result.username))
            user_id = result.id
            second = random.randint(2, 15)
            await sleep(second)
            delete_user = await self.app.delete_contacts(user_id)  # удаление контакта
        text_result = '\n'.join(result_usernames)
        await self.app.send_message(message.chat.id, text_result)
        return

    async def listener_get_phone(self, client: Client, message: types.Message) -> None:
        """
        Метод для обработки сообщения с телефонным номером и запуска отправки сообщения.
        :param client: клиент
        :param message: сообщение
        :return: none
        """
        logger.debug(f"Получено сообщение от пользователя: {message.chat.id} с текстом: <{message.text}>")
        text_command = message.text
        is_setuser = self.__set_user_id(text_command, type_fun='phone')
        if is_setuser == 2:
            logger.info(f"Пользователь c id: {text_command.split(':')[-1]} успешно установлен и сохранен.")
            await self.app.send_message(message.chat.id, 'Пользователь установлен.')
            return
        elif is_setuser == 1:
            logger.warning(f'Введена неверная команда: <{text_command}>')
            await self.app.send_message(message.chat.id, 'Неверная команда. Пример: ":setuser: 1234567"')
            logger.debug("Сообщение о неверной команде отправлено пользователю")
            return
        text = re.sub("[-()+ ]", "", message.text)
        print(text)
        text_phones = text.split('\n')
        print(text_phones)
        for text_phone in text_phones:
            result = await self.get_info_user(text_phone)
            if result is None:
                # результат пустой, т.е. пользователя не удалось найти
                text_result = 'Не обнаружен пользователь с привязкой к номеру ' + text_phone
                logger.debug(text_result)
                await self.app.send_message(message.chat.id, text_result)
                logger.debug("Сообщение с результатом отправлено пользователю")
                second = random.randint(2, 15)
                await sleep(second)
                continue
            user_id, user_usernames, phone = result.id, result.username, result.phone
            text_result = f'Id: {user_id}\nUsername: {user_usernames}\nPhone: {phone}\n'
            delete_user = await self.app.delete_contacts(user_id)  # удаление контакта
            last_name, first_name = delete_user.last_name, delete_user.first_name  # получение имени пользователя
            text_result += f'Name: {first_name} {last_name}'
            logger.debug("Пользователь успешно найден.")
            logger.debug(text_result)
            user = {
                'id': str(user_id),
                'username': user_usernames,
                'first_name': first_name,
                'last_name': last_name,
                'phone': phone
            }
            self.__save_user(user)
            logger.debug("Пользователь успешно записан в БД.")
            await self.app.send_message(message.chat.id, text_result)
            logger.debug("Сообщение с результатом отправлено пользователю")
            second = random.randint(2, 15)
            await sleep(second)
        return

    def run(self) -> None:
        """
        Метод запуска работы бота.
        :return: None
        """
        logger.debug('Бот запущен и работает.')
        try:
            self.app.run()
        except Exception as error:
            logger.critical("Непредвиденная ошибка в работе бота.")
            logger.critical(error)
        return

    def __save_user(self, user_info: Dict[str, str]):
        """
        Метод сохранения результата в БД.
        :param user_info: Словарь с ифнормацией о пользователе.
        :return:
        """
        query = INSERT_USER.format(id_tg=user_info['id'],
                                   username=user_info['username'],
                                   first_name=user_info['first_name'],
                                   last_name=user_info['last_name'],
                                   phone=user_info['phone'])
        self.db.run(query, type='insert')
        return

    async def get_result(self, phone: str) -> None:
        """
        Метод для получения информации о пользователе в телеграмм без запуска бота.
        Пример:
            client.app.run(client.get_result('79111111111'))
        :param phone: номер телефона, по которому осуществляется поиск
        :return: None, результат записывается в переменную self.__result.
                 Для получения результата обратиться:
                    > client.result
        """
        self.__result = None
        text_phone = re.sub("[-()+ ]", "", phone)
        async with self.app:
            user = await self.get_info_user(text_phone)
            if user is None:
                # результат пустой, т.е. пользователя не удалось найти
                text_result = 'Не обнаружен пользователь с привязкой к номеру ' + text_phone
                logger.debug(text_result)
                return
            self.__result = {
                'id': user.id,
                'username': user.username,
                'phone': user.phone
            }
            delete_user = await self.app.delete_contacts(self.__result['id'])  # удаление контакта
            self.__result['name'] = f'{delete_user.first_name} {delete_user.last_name}'
            self.__result['first_name'] = delete_user.first_name
            self.__result['last_name'] = delete_user.last_name
            logger.debug("Пользователь успешно найден.")
            logger.debug(self.__result)
        return


if __name__ == '__main__':
    client = GetUsernameBot(config.API_ID_GET_USERNAME, config.API_HASH_GET_USERNAME, False)
    # пример запуска бота в режиме бота
    # client.run()
    #
    # пример запуска бота в режиме получения телефона
    client.app.run(client.get_result('79118528152'))
    print(client.result)
