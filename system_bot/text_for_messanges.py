"""
Файл с шаблонами сообщений для технического канала.
"""

ADD_USER_ADMIN = """
#НОВЫЙ_УЧАСТНИК
1. Пользователя добавил - {admin_name} [{admin_id}];
2. Новый пользователь - {user_name} [{user_id}];
3. Группа: {group_name} [{group_id}];
4. Дата события: {date};
5. Кто: #ID{admin_id};
6. Кого: #ID{user_id};
7. Куда: #ID{group_id_find};
8. #{group_admin_id_find};
9. #{group_user_id_find};
"""

LEFT_USER_ADMIN = """
#ВЫХОД_УЧАСТНИКА
1. Пользователя удалил - {admin_name} [{admin_id}];
2. Ушедший пользователь - {user_name} [{user_id}];
3. Группа: {group_name} [{group_id}];
4. Дата события: {date};
5. Кто: #ID{admin_id};
6. Кого: #ID{user_id};
7. Откуда: #ID{group_id_find};
8. #{group_admin_id_find};
9. #{group_user_id_find};
"""

MEMBER_PERMISSIONS_CHANGED_USER = """
#ОГРАНИЧЕНИЕ_УЧАСТНИКА
1. Кто ограничил - {admin_name} [{admin_id}];
2. Кого ограничили - {user_name} [{user_id}];
3. {permissions}
4. Группа: {group_name} [{group_id}];
5. Дата события: {date};
6. Кто: #ID{admin_id};
7. Кого: #ID{user_id};
8. Откуда: #ID{group_id_find};
9. #{group_admin_id_find};
10. #{group_user_id_find};
"""


EXIT_USER_TEXT = '''
Здравствуйте, Вы удалились из группы {title_group}. 
Администратор группы просит связаться с ним.
Напишите, пожалуйста ему в лс. {admin_name} Спасибо!
'''

STATIC_TEXT = """
#СТАТИСТИКА
1. Группа: {group_name} [{group_id}];
2. Дата: {date};
3. Добавилось: {count_join} человек:
{list_users_join}
4. Вышло: {count_left} человек:
{list_users_left}
5. Прирост/убыль: {raz}.
"""
