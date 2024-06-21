import os
import random
from asyncio import sleep
from typing import Optional, List, Dict, NoReturn

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram import Client, types, filters
from pyrogram.errors import MessageIdInvalid
from pyrogram.handlers import MessageHandler
from loguru import logger

from dbEditor import SqlLiteEditor
from sql_queries import *
import config


class SendMessageChanelBot:
    """
    Телеграмм-юзербот, который берет новое сообщение в телеграмм чатах и пересылает его в другой телегамм чат.
    Создание экземпляра класса:
        > bot = SendMessageChanelBot(api_id, api_hash)
    """
    def __init__(self, api_id: Optional[str] = None, api_hash: Optional[str] = None) -> NoReturn:
        """
        Инициализация объекта класса для управления ЮзерБотом.
        :param api_id: инициализирующий параметр для работы телеграмм api
        :param api_hash: инициализирующий параметр для работы телеграмм api
        """
        logger.add('./forward_messages_bot_1/logs/debug.log',
                   format="{time}| {level}| {message}",
                   level="DEBUG",
                   rotation='10 MB',
                   encoding='utf-8',
                   compression='zip')
        self.api_id: Optional[str] = api_id
        self.api_hash: Optional[str] = api_hash
        if self.api_id is None or self.api_id is None:
            # Если не переданны api_hash или api_id, то ошибка
            logger.error("Проверьте параметры api_hash, api_id.")
            raise ValueError

        try:
            self.app = Client('sendMessagesBot', api_id=self.api_id, api_hash=api_hash)
        except Exception as error:
            logger.error("Не удалось установить соединение с клиентом телеграмм:")
            logger.error(error)
            return
        # self.db_name = 'database_usernames.db'  # база данных для сохранения каналов
        self.db_name = './admin_site/db.sqlite3'  # база данных для сохранения каналов
        create_db = os.path.isfile(self.db_name)
        try:
            self.db = SqlLiteEditor(self.db_name)  # Подключение к базе данных
        except Exception as error:
            self.db.close()
            logger.error("Не удалось установить подлкючение к базе:")
            logger.error(error)
            return
        if not create_db:
            # создание таблицы для юзеров
            self.db.run(CREATE_TABLE, 'create')
            logger.debug("Создана таблица для хранения допустимых пользователей.")
        self.dict_ids_handler = {}  # словарь для хранения хэндлеров
        self.check_groups = []  # список для хранения проверяемых групп
        self.tech_groups = {}  # словарь для хранения технических групп
        if create_db:
            # если база данных была уже, то перебор всех пользоателей и создание слушателей
            self.check_db()
        # таймер
        self.scheduler = None
        self.__create_scheduler()
        logger.debug(f"Создан экземпляр класса.")
        return

    def __create_scheduler(self) -> NoReturn:
        """
        Метод для создания таймера прослушивания базы данных каждую минуту.
        """
        self.scheduler = AsyncIOScheduler()
        self.scheduler.add_job(self.check_db, "interval", seconds=60)
        return

    def check_db(self) -> NoReturn:
        """
        Метод прослушивания базы данных для установки новых каналов.
        """
        # logger.info("Запуск проверки базы данных.")
        groups = self.db.run(SELECT_IDS, 'select')
        self.tech_groups = {int(i['id_chat']): i['username_chat'] for i in groups if i['tech_chat'] == 1}
        groups_id_new = [int(i['id_chat']) for i in groups if i['tech_chat'] == 0]
        groups_id_old = list(self.dict_ids_handler.keys())
        delete_id = list(set(groups_id_old) - set(groups_id_new))
        add_id = list(set(groups_id_new) - set(groups_id_old))
        for i in delete_id:
            # удаление групп
            self.app.remove_handler(self.dict_ids_handler[i])
            logger.debug(f"Удален мониторинг группы с id: {i}")
            self.dict_ids_handler.pop(i)
        for i in add_id:
            # добавление групп
            message_handler_new = MessageHandler(self.listener_forward_message, filters=filters.chat(i))
            self.dict_ids_handler[i] = message_handler_new
            self.app.add_handler(self.dict_ids_handler[i])
            logger.debug(f"Добавлен мониторинг группы с id: {i}")
        return

    async def __send_message_tech(self, message):
        """
        Технический метод отправления сообщения в технические каналы.
        :param message: Сообщение для отправки
        """
        await sleep(2)
        messages = [message]
        for tech_id in self.tech_groups.keys():
            for mes in messages:
                await sleep(2)
                await self.app.send_message(tech_id, mes)
        return

    async def listener_forward_message(self, client: Client, message: types.Message) -> NoReturn:
        """
        Метод обработки нового сообщения в чате.
        """
        # print(message)
        # second = random.randint(2, 15)
        # await sleep(second)
        # await self.app.forward_messages(chat_id=6699760918, from_chat_id=message.chat.id, message_ids=[message.id])
        for id, name in self.tech_groups.items():
            second = random.randint(2, 15)
            await sleep(second)
            title = message.chat.title
            try:
                # Отправка сообщения из канала в канал
                await self.app.forward_messages(chat_id=id, from_chat_id=message.chat.id, message_ids=[message.id])
                logger.debug(f"Сообщение из группы {title} пересланно в группу {name}.")
            except MessageIdInvalid:
                logger.debug(f"Битое сообщение в чате {title}, id: {id}")
                continue
        return

    def run(self) -> NoReturn:
        """
        Метод запуска работы бота.
        Пример:
            > bot.run()
        """
        logger.debug('Бот запущен и работает.')
        try:
            self.scheduler.start()
            self.app.run()
        except Exception as error:
            logger.critical("Непредвиденная ошибка в работе бота.")
            logger.critical(error)
        return


if __name__ == "__main__":
    bot = SendMessageChanelBot(config.API_ID, config.API_HASH)
    bot.run()

