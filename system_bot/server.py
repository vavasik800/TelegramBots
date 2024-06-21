__date__ = '18-09-2023'

import datetime
from asyncio import sleep
import time
from json import loads
import random

import pyrogram
from pyrogram import Client, types, filters
from pyrogram.enums import ChatEventAction, ChatType, ChatMemberStatus
from pyrogram.handlers import MessageHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import config
import queries
import text_for_messanges
from dbEditor import SqlLiteEditor


class SystemBot:
    """
    Телеграмм-юзерБот для отслеживания административных логов каналов и групп и копирования сообщений
    о добавлении новых пользователей, удаления пользователей и ограничении их прав.
    """

    def __init__(self, db_name: str = None):
        """
        Конструктор для создания экземпляра класса
        :param db_name: Имя файла базы данных
        """
        self.db_name = db_name
        self.db = SqlLiteEditor(self.db_name)  # Подключение к базе данных
        try:
            for query_create_table in queries.CREATE_TABLE_EVENTS.split(';'):
                self.db.run(query_create_table, type='create')
        except Exception as error:
            print(error)
        if not self.db_name:
            # Создаем таблицы для бота
            for query_create_table in queries.CREATE_TABLES.split(';'):
                self.db.run(query_create_table, type='create')
        # self.my_id = int(config.MY_ID)  # id для работы с каналами
        self.techs_id = None
        self.groups_id = None
        # Заполнение каналов
        self.get_chats()
        print('техническое id', self.techs_id)
        # # группы для просмотра
        # self.groups_id = [row.get('id_group') for row in self.db.run(queries.SELECT_ALL_CHANELS_FROM_ADMIN, type='select')]
        # имя администратора
        self.name_admin = [row.get('username_admin') for row in self.db.run(queries.SELECT_USERNAME_ADMIN, type='select')]
        self.name_admin = self.name_admin[0] if len(self.name_admin) > 0 else ''
        # клиент для работы с Ботом
        answer = self.db.run(query=queries.SELECT_API_DATA, type='select')
        api_id = answer[0].get('api_id')
        api_hash = answer[0].get('api_hash')
        self.app = Client('admin', api_id=api_id, api_hash=api_hash)
        # словарь с шаблонами для сообщений в технический канал
        self.dict_templates = {
            'member_joined': text_for_messanges.ADD_USER_ADMIN,
            'member_left': text_for_messanges.LEFT_USER_ADMIN,
            'member_permissions_changed': text_for_messanges.MEMBER_PERMISSIONS_CHANGED_USER,
            'static': text_for_messanges.STATIC_TEXT
        }
        # словарь для расшифровки ограничений пользователей
        self.permissions_dict = {
            'can_send_messages': '#отправка_сообщений_',
            'can_send_media_messages': '#отправка_медиа_сообщений_',
            'can_send_other_messages': '#отправка_других_сообщений_',
            'can_send_polls': '#отправка_опросов_',
            'can_add_web_page_previews': '#добавление_веб_страниц_',
            'can_change_info': '#изменение_настроек_чата_',
            'can_invite_users': '#добавление_пользователей_',
            'can_pin_messages': '#закрепление_сообщений_',
        }
        # таймер
        self.scheduler = None
        self.__create_handlers()

    def get_chats(self):
        self.techs_id = [row.get('id_chat') for row in self.db.run(queries.SELECT_TECH_CHANEL_FROM_ADMIN, type='select')]
        a = []
        for tech_id in self.techs_id:
            try:
                id_int = int(tech_id)
            except ValueError:
                print('Недопустимое значение id-чата')
                continue
            a.append(id_int)
        self.techs_id = a

        self.groups_id = [row.get('id_chat') for row in self.db.run(queries.SELECT_ALL_CHANELS_FROM_ADMIN, type='select')]
        a = []
        for group_id in self.groups_id:
            try:
                id_int = int(group_id)
            except ValueError:
                print('Недопустимое значение id-чата')
                continue
            a.append(id_int)
        self.groups_id = a
        return

    def run(self):
        """
        Основной метод запуска сервера бота.
        """
        self.scheduler.start()
        self.app.run()

    def create_message_new(self, params: dict, type: str) -> str:
        """
        Создание сообщения для отправки в технический канал
        :param params: словарь параметров
        :param type: тип events
        :return: сообщение для технического канала
        """
        tmp = self.dict_templates[type]
        message_text = tmp.format(**params)
        return message_text.replace(' -  []', '')

    # async def message_admin(self, client: Client, message: types.Message):
    #     """
    #     Метод для работы с сообщениями, поступающими в нужный id
    #     """
    #     text = message.text.lower()
    #     if 'технический' in text or 'добавить' in text:
    #         # случай для добавления и сохранения каналов
    #         chat_name = text.split(':')[-1]
    #         try:
    #             chat = await self.app.get_chat(chat_name)  # получение чата
    #             chat_name, chat_id, chat_type = chat.username, chat.id, chat.type.value
    #             print(chat_type)
    #             if 'технический' in text:
    #                 # добавление технического канала
    #                 if chat_id in self.techs_id:
    #                     await message.reply_text('Данный технический канал уже установлен.')
    #                     return
    #                 query_insert_chat = queries.INSERT_GROUP.format(name=chat_name, id_group=chat_id, type=chat_type,
    #                                                                 technic='true')
    #                 self.techs_id.append(chat_id)
    #                 await message.reply_text('Технический канал установлен.')
    #                 return
    #             elif 'добавить' in text:
    #                 # случай для добавления любого другого канала
    #                 if chat_name in self.groups_id:
    #                     await message.reply_text('Данный канал уже просматривается')
    #                     return
    #                 query_insert_chat = queries.INSERT_GROUP.format(name=chat_name, id_group=chat_id, type=chat_type,
    #                                                                 technic='false')
    #                 self.groups_id.append(chat_name)
    #             self.db.run(query_insert_chat, type='insert')  # добавление каналов в Базу данных
    #             await message.reply_text('Канал установлен для просмотра.')
    #         except ValueError:
    #             await message.reply_text('Проверьте название канала. Канал не найден.')
    #         return

    @staticmethod
    def __create_find_ind(chat, id_user, username_user, id_admin, username_admin):
        if id_admin == '' and username_admin == '':
            group_admin_id_find = ''
        else:
            group_admin_id_find = chat.username if chat.username is not None else chat.title.replace(' ', '')
            group_admin_id_find += '_'
            group_admin_id_find += username_admin if username_admin is not None else str(id_admin)
        group_user_id_find = chat.username if chat.username is not None else chat.title.replace(' ', '')
        group_user_id_find += '_'
        group_user_id_find += username_user if username_user is not None else str(id_user)
        return group_admin_id_find, group_user_id_find

    async def admin_log(self):
        """
        Метод для просмотра административных логов каналов
        """
        print('ЗАПУСК ПРОВЕРКИ')
        self.get_chats()
        chat_names = self.groups_id
        if len(self.techs_id) == 0:
            print('Нет технического канала')
            return
        for chat_name in chat_names:
            # перебор чатов для просмотра логов
            chat = await self.app.get_chat(chat_name)  # информация о чате
            permis = chat.permissions
            print(permis)
            chat_id = chat.id
            chat_type = chat.type
            admin_log = self.app.get_chat_event_log(chat_id)  # получение административных логов
            print('Обработка чата')
            print(chat_name, chat_id)
            messages_for_send = []
            async for event in admin_log:
                try:
                    # перебор административных событий
                    type_event = event.action
                    query = queries.SELECT_EVENT_ID.format(hash=event.id)  # запрос для получения хэша события
                    event_in_db = self.db.run(query, type='select')
                    print(event_in_db)
                    if len(event_in_db) != 0:
                        # случай когда событие уже просматривалось
                        break
                    print('Обнаружено новое событие!')
                    # print(event)
                    try:
                        type = type_event.value
                    except AttributeError:
                        type = type_event
                    hash, date = event.id, event.date
                    print(type)
                    if type_event == ChatEventAction.MEMBER_JOINED or type == 'ChatEventAction.UNKNOWN-types.ChannelAdminLogEventActionParticipantJoinByInvite':
                        # Случай когда пользователь сам пришел в канал
                        id_user = event.user.id
                        username_user = event.user.username
                        type = ChatEventAction.MEMBER_JOINED.value
                        query_insert = queries.INSERT_EVENT.format(hash=hash, type_event=type, id_user=id_user,
                                                                   username_user=username_user,
                                                                   id_group=chat_id, datetime=date, id_admin='',
                                                                   username_admin='')
                        print('Добавлен участник.')
                        group_admin_id_find, group_user_id_find = self.__create_find_ind(chat, id_user, username_user,
                                                                                         '', '')
                        params_for_message = {
                            'admin_name': '',
                            'admin_id': '',
                            'user_name': f'@{username_user}' if username_user is not None else '',
                            'user_id': id_user,
                            'date': date,
                            'group_name': chat.username if chat.username is not None else chat.title,
                            'group_id': chat_id,
                            'group_id_find': str(chat_id).replace('-', ''),
                            'group_admin_id_find': group_admin_id_find,
                            'group_user_id_find': group_user_id_find
                        }
                        text_message = self.create_message_new(params_for_message, type)
                        print(text_message)
                        self.db.run(query_insert, 'insert')
                        messages_for_send.append(text_message)
                        continue
                    if type_event == ChatEventAction.MEMBER_INVITED:
                        # Случай добавления пользователя в чат администратором
                        id_admin = event.user.id
                        username_admin = event.user.username
                        id_user = event.invited_member.user.id
                        username_user = event.invited_member.user.username
                        query_insert = queries.INSERT_EVENT.format(hash=hash,
                                                                   type_event=ChatEventAction.MEMBER_JOINED.value,
                                                                   id_user=id_user,
                                                                   username_user=username_user,
                                                                   id_group=chat_id, datetime=date, id_admin=id_admin,
                                                                   username_admin=username_admin)
                        print('Добавлен новый участник.')
                        group_admin_id_find, group_user_id_find = self.__create_find_ind(chat,
                                                                                         id_user,
                                                                                         username_user,
                                                                                         id_admin,
                                                                                         username_admin)
                        params_for_message = {
                            'admin_name': f'@{username_admin}' if username_admin is not None else '',
                            'admin_id': id_admin,
                            'user_name': f'@{username_user}' if username_user is not None else '',
                            'user_id': id_user,
                            'date': date,
                            'group_name': chat.username if chat.username is not None else chat.title,
                            'group_id': chat_id,
                            'group_id_find': str(chat_id).replace('-', ''),
                            'group_admin_id_find': group_admin_id_find,
                            'group_user_id_find': group_user_id_find
                        }
                        text_message = self.create_message_new(params_for_message, ChatEventAction.MEMBER_JOINED.value)
                        print(text_message)
                        self.db.run(query_insert, 'insert')
                        messages_for_send.append(text_message)
                        continue
                    if type_event == ChatEventAction.MEMBER_LEFT:
                        # Случай, когда пользователь сам вышел из канала
                        id_user = event.user.id
                        username_user = event.user.username
                        query_insert = queries.INSERT_EVENT.format(hash=hash, type_event=type, id_user=id_user,
                                                                   username_user=username_user,
                                                                   id_group=chat_id, datetime=date, id_admin='',
                                                                   username_admin='')
                        print('Участник покинул канал.')
                        group_admin_id_find, group_user_id_find = self.__create_find_ind(chat, id_user, username_user,
                                                                                         '', '')
                        params_for_message = {
                            'admin_name': '',
                            'admin_id': '',
                            'user_name': f'@{username_user}' if username_user is not None else '',
                            'user_id': id_user,
                            'date': date,
                            'group_name': chat.username if chat.username is not None else chat.title,
                            'group_id': chat_id,
                            'group_id_find': str(chat_id).replace('-', ''),
                            'group_admin_id_find': group_admin_id_find,
                            'group_user_id_find': group_user_id_find
                        }
                        text_message = self.create_message_new(params_for_message, type)
                        print(text_message)
                        self.db.run(query_insert, 'insert')
                        messages_for_send.append(text_message)
                        continue
                    if type_event == ChatEventAction.MEMBER_PERMISSIONS_CHANGED:
                        # Случай изменения прав пользователя
                        id_user = event.old_member_permissions.user.id
                        username_user = event.old_member_permissions.user.username
                        id_admin = event.user.id
                        username_admin = event.user.username
                        if event.new_member_permissions.status == ChatMemberStatus.BANNED:
                            # Удаление пользователя администратором
                            print('Участник покинул канал')
                            query_insert = queries.INSERT_EVENT.format(hash=hash,
                                                                       type_event=ChatEventAction.MEMBER_LEFT.value,
                                                                       id_user=id_user,
                                                                       username_user=username_user,
                                                                       id_group=chat_id, datetime=date,
                                                                       id_admin=id_admin,
                                                                       username_admin=username_admin)
                            group_admin_id_find, group_user_id_find = self.__create_find_ind(chat, id_user,
                                                                                             username_user,
                                                                                             id_admin,
                                                                                             username_admin)
                            params_for_message = {
                                'admin_name': f'@{username_admin}' if username_admin is not None else '',
                                'admin_id': id_admin,
                                'user_name': f'@{username_user}' if username_user is not None else '',
                                'user_id': id_user,
                                'date': date,
                                'group_name': chat.username if chat.username is not None else chat.title,
                                'group_id': chat_id,
                                'group_id_find': str(chat_id).replace('-', ''),
                                'group_admin_id_find': group_admin_id_find,
                                'group_user_id_find': group_user_id_find
                            }
                            text_message = self.create_message_new(params_for_message,
                                                                   ChatEventAction.MEMBER_LEFT.value)
                            print(text_message)
                            self.db.run(query_insert, 'insert')
                            messages_for_send.append(text_message)
                            continue
                        if event.old_member_permissions.status == ChatMemberStatus.BANNED:
                            continue
                        query_insert = queries.INSERT_EVENT.format(hash=hash, type_event=type, id_user=id_user,
                                                                   username_user=username_user,
                                                                   id_group=chat_id, datetime=date, id_admin=id_admin,
                                                                   username_admin=username_admin)
                        print('Изменены настройки пользователей')
                        new_permissions = event.new_member_permissions.permissions
                        old_permissions = event.old_member_permissions.permissions
                        json_new_permissions = loads(str(new_permissions)) if new_permissions is not None else None
                        json_old_permissions = loads(str(old_permissions)) if old_permissions is not None else loads(str(permis))
                        m = ''
                        print(json_new_permissions)
                        print(json_old_permissions)
                        if json_old_permissions is None:
                            for (new_key, new_value) in json_new_permissions.items():
                                if new_key == '_':
                                    continue
                                m += self.permissions_dict[new_key]
                                m += 'да' if new_value else 'нет'
                                m += '; '
                        else:
                            for (new_key, new_value) in json_new_permissions.items():
                                old_value = json_old_permissions[new_key]
                                if old_value == new_value:
                                    continue
                                m += self.permissions_dict[new_key]
                                m += 'да' if new_value else 'нет'
                                m += '; '
                        if m == '':
                            query_insert = queries.INSERT_EVENT.format(hash=hash,
                                                                       type_event=ChatEventAction.MEMBER_JOINED.value,
                                                                       id_user=id_user,
                                                                       username_user=username_user,
                                                                       id_group=chat_id, datetime=date,
                                                                       id_admin=id_admin,
                                                                       username_admin=username_admin)
                            print('Добавлен новый участник.')
                            group_admin_id_find, group_user_id_find = self.__create_find_ind(chat, id_user,
                                                                                             username_user,
                                                                                             id_admin,
                                                                                             username_admin)
                            params_for_message = {
                                'admin_name': f'@{username_admin}' if username_admin is not None else '',
                                'admin_id': id_admin,
                                'user_name': f'@{username_user}' if username_user is not None else '',
                                'user_id': id_user,
                                'date': date,
                                'group_name': chat.username if chat.username is not None else chat.title,
                                'group_id': chat_id,
                                'group_id_find': str(chat_id).replace('-', ''),
                                'group_admin_id_find': group_admin_id_find,
                                'group_user_id_find': group_user_id_find
                            }
                            text_message = self.create_message_new(params_for_message,
                                                                   ChatEventAction.MEMBER_JOINED.value)
                            print(text_message)
                            self.db.run(query_insert, 'insert')
                            messages_for_send.append(text_message)
                            continue
                        group_admin_id_find, group_user_id_find = self.__create_find_ind(chat, id_user,
                                                                                         username_user,
                                                                                         id_admin,
                                                                                         username_admin)
                        params_for_message = {
                            'admin_name': f'@{username_admin}' if username_admin is not None else '',
                            'admin_id': id_admin,
                            'user_name': f'@{username_user}' if username_user is not None else '',
                            'user_id': id_user,
                            'date': date,
                            'permissions': m,
                            'group_name': chat.username if chat.username is not None else chat.title,
                            'group_id': chat_id,
                            'group_id_find': str(chat_id).replace('-', ''),
                            'group_admin_id_find': group_admin_id_find,
                            'group_user_id_find': group_user_id_find
                        }
                        text_message = self.create_message_new(params_for_message, type)
                        print(text_message)
                        self.db.run(query_insert, 'insert')
                        messages_for_send.append(text_message)
                        continue
                except Exception as error:
                    print('Непредвиденная ошибка')
                    print(error)
            print(f'Перебор логов чата {chat_name} закончен.')
            print(f'Всего {len(messages_for_send)} новых логов.')
            print(f'Началась отправка сообщений в технический канал.')
            messages_for_send = messages_for_send[::-1]
            for mes in messages_for_send:
                try:
                    await self.__send_message_tech(mes)
                except Exception as error:
                    print('Непредвиденная ошибка')
                    print(error)
            print(f'Законичилась отправка сообщений в технический канал.')
        return

    async def __send_message_tech(self, message):
        """
        Технический метод отправления сообщения в технические каналы.
        :param message: Сообщение для отправки
        """
        sec = random.randint(5,30)
        await sleep(sec)
        messages = [message]
        # Если сообщение > 4095, то нарезаем его (т.к. апи телеграм не поддерживает большие сообщения)
        if len(message) > 4095:
            messages = [message[i * 4095:(i + 1) * 4095] for i in range(len(message) // 4095 + 1)]
        for tech_id in self.techs_id:
            for index, mes in enumerate(messages):
                if index > 0:
                   sec = random.randint(5,30)
                   await sleep(sec)
                await self.app.send_message(tech_id, mes)

    async def get_static(self):
        date_now = datetime.datetime.now() - datetime.timedelta(days=1)
        date_now_str = date_now.strftime('%Y-%m-%d')
        print('ЗАПУСК ПРОВЕРКИ СТАТИСТИКИ')
        self.get_chats()
        chats_id = self.groups_id
        if len(self.techs_id) == 0:
            print('Нет технического канала')
            return
        for chat_id in chats_id:
            chat = await self.app.get_chat(chat_id)  # информация о чате
            query_count_join = queries.SELECT_COUNT_EVENT_JOIN.format(date=date_now_str,
                                                                      id_group=chat.id)
            query_count_left = queries.SELECT_COUNT_EVENT_LEFT.format(date=date_now_str,
                                                                      id_group=chat.id)
            query_username_join = queries.SELECT_USERNAME_JOIN.format(date=date_now_str,
                                                                      id_group=chat.id)
            query_username_left = queries.SELECT_USERNAME_LEFT.format(date=date_now_str,
                                                                      id_group=chat.id)
            count_join = self.db.run(query_count_join, type='select')
            count_join = count_join[0].get('count') if count_join[0].get('count') is not None else '0'
            list_username_join = [row.get('username_user') for row in self.db.run(query_username_join, type='select') if row.get('username_user') != 'None']
            count_left = self.db.run(query_count_left, type='select')
            count_left = count_left[0].get('count') if count_left[0].get('count') is not None else '0'
            list_username_left = [row.get('username_user') for row in self.db.run(query_username_left, type='select') if row.get('username_user') != 'None']

            params_for_message = {
                'date': date_now.strftime('%d.%m.%Y'),
                'group_name': chat.username if chat.username is not None else chat.title,
                'group_id': chat.id,
                'count_join': count_join,
                'count_left': count_left,
                'list_users_join': '\n'.join(list_username_join),
                'list_users_left': '\n'.join(list_username_left),
                'raz': int(count_join) - int(count_left)
            }
            text_message = self.create_message_new(params_for_message, 'static')
            print(text_message)
            try:
                await self.__send_message_tech(text_message)
                print("Отправлено сообщение статистики в канал.")
            except Exception as error:
                print('Непредвиденная ошибка')
                print(error)
        return

    def __create_handlers(self):
        """
        Технический метод для создания таймера и хэндлера для прослушивания сообщений установки каналов
        """
        # self.__admin_message_handler = MessageHandler(self.message_admin, filters=filters.chat(self.my_id))
        # self.app.add_handler(self.__admin_message_handler)
        self.scheduler = AsyncIOScheduler()
        # self.scheduler.add_job(self.admin_log, "interval", seconds=60*60*4)
        self.scheduler.add_job(self.get_static, 'cron', hour=2, minute=0)
        self.scheduler.add_job(self.admin_log, 'cron', hour=1, minute=0)
        self.scheduler.add_job(self.admin_log, 'cron', hour=5, minute=0)
        self.scheduler.add_job(self.admin_log, 'cron', hour=13, minute=0)
        self.scheduler.add_job(self.admin_log, 'cron', hour=21, minute=0)

        # self.scheduler.add_job(self.admin_log, "interval", seconds=60*60*4)
        return


if __name__ == '__main__':
    app = SystemBot(config.PATH_DB)
    app.run()

