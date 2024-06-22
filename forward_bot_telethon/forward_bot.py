import os
import random
from asyncio import sleep
from typing import Optional, NoReturn

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telethon import TelegramClient, events
from loguru import logger

from dbEditor import SqlLiteEditor
from sql_queries import *
import config


class SendMessageChanelBot:
    """
    Телеграмм-юзербот, который берет новое сообщение в телеграмм чатах и пересылает его в другой телегамм чат.
    Используется библиотека telethon.
    Создание экземпляра класса:
        > bot = SendMessageChanelBot(api_id, api_hash)
    """
    col_name_id_channel = config.COLUMN_ID_CHANEL
    col_name_name_channel = config.COLUMN_NAME_CHANEL
    col_name_tech_chanel = config.COLUMN_TECH_CHANEL

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
            # Если не переданы api_hash или api_id, то ошибка
            logger.error("Проверьте параметры api_hash, api_id.")
            raise ValueError
        self.db_name = config.DB_PATH  # база данных для сохранения каналов
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
        try:
            self.app = TelegramClient('forward_bot.session', api_id=self.api_id, api_hash=api_hash, system_version="4.16.30-vxCUSTOM")
            self.app.start()
        except Exception as error:
            logger.error("Не удалось установить соединение с клиентом телеграмм:")
            logger.error(error)
            return
        self.dict_ids_handler = {}  # словарь для хранения хэндлеров
        self.check_groups = []  # список для хранения проверяемых групп
        self.tech_groups = {}  # словарь для хранения технических групп
        print("Create data")
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
        self.scheduler.add_job(self.check_db, "interval", seconds=120)
        return

    def check_db(self) -> NoReturn:
        """
        Метод прослушивания базы данных для установки новых каналов.
        """
        logger.info("Запуск проверки базы данных.")
        groups = self.db.run(SELECT_IDS, 'select')
        self.tech_groups = {int(i[self.col_name_id_channel]): i[self.col_name_name_channel] for i in groups if i[self.col_name_tech_chanel] == 1}
        groups_id_new = [int(i[self.col_name_id_channel]) for i in groups if i[self.col_name_tech_chanel] == 0]
        groups_id_old = list(self.dict_ids_handler.keys())
        delete_id = list(set(groups_id_old) - set(groups_id_new))
        add_id = list(set(groups_id_new) - set(groups_id_old))
        for i in delete_id:
            # удаление групп
            self.app.remove_event_handler(self.dict_ids_handler[i])
            logger.debug(f"Удален мониторинг группы с id: {i}")
            self.dict_ids_handler.pop(i)
        for i in add_id:
            # добавление групп
            message_handler_new = self.listener_forward_message
            self.dict_ids_handler[i] = message_handler_new
            self.app.add_event_handler(self.dict_ids_handler[i], events.NewMessage(chats=[i]))
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

    async def listener_forward_message(self, event) -> NoReturn:
        """
        Метод обработки нового сообщения в чате.
        """
        for id, name in self.tech_groups.items():
            second = random.randint(2, 15)
            await sleep(second)
            message = event.message
            title = message.chat.title
            try:
                # Отправка сообщения из канала в канал
                await self.app.forward_messages(id, message)
                logger.debug(f"Сообщение из группы {title} пересланно в группу {name}.")
            except Exception as error:
                logger.debug(error)
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
            self.app.run_until_disconnected()
        except Exception as error:
            logger.critical("Непредвиденная ошибка в работе бота.")
            logger.critical(error)
        return


