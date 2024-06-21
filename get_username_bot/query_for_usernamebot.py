CREATE_TABLE = """
create table idUser
(
    id         integer
        constraint events_pk
            primary key autoincrement,
    id_user TEXT
);
create table users 
(
    id         integer
        constraint events_pk
            primary key autoincrement,
    id_tg TEXT  UNIQUE ON CONFLICT IGNORE,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    phone TEXT,
    info TEXT
)
"""

INSERT_USER = """
insert into users (id_tg, username, first_name, last_name, phone) values ('{id_tg}', '{username}', '{first_name}', '{last_name}', '{phone}')
"""

INSERT_ID = """
insert into idUser (id_user) values ('{id_user}');
"""

SELECT_IDS = """
select id_user
from idUser;
"""


