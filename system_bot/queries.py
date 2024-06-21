"""
Файл с шаблонами Sql-запросов для бота.
"""

CREATE_TABLE_EVENTS = """
create table events
(
    id         integer
        constraint events_pk
            primary key autoincrement,
    type_event TEXT,
    id_user    TEXT,
    username_user TEXT,
    id_group   TEXT,
    datetime   TEXT,
    id_admin   TEXT,
    username_admin TEXT,
    hash       TEXT
);
"""

CREATE_TABLES = """
create table groups
(
    id       integer not null
        constraint groups_pk
            primary key autoincrement,
    name     TEXT,
    id_group TEXT,
    type     TEXT,
    technic  BLOB default FALSE
);

create table events
(
    id         integer
        constraint events_pk
            primary key autoincrement,
    type_event TEXT,
    id_user    TEXT,
    username_user TEXT,
    id_group   TEXT,
    datetime   TEXT,
    id_admin   TEXT,
    username_admin TEXT,
    hash       TEXT
);

create table admins
(
    id         integer
        constraint admins_pk
            primary key autoincrement,
    username TEXT,
    id_user    TEXT,
    active BLOB default FALSE
);
"""

INSERT_GROUP = """
insert into groups (name, id_group, type, technic) values ('{name}', '{id_group}', '{type}', {technic})
"""

SELECT_TECH_CHANEL_FROM_ADMIN = """
select distinct id_chat
from forward_app_channels
where tech_chat=true
"""

SELECT_TECH_CHANEL = """
select distinct name, id_group, type, technic
from groups
where technic=true
"""

SELECT_ALL_CHANELS_FROM_ADMIN = """
select distinct id_chat
from forward_app_channels
where tech_chat=false
"""

SELECT_USERNAME_ADMIN = """
select username_admin
from forward_app_adminforlog
"""

SELECT_API_DATA = """
select api_hash, api_id
from forward_app_adminforlog
"""

SELECT_ALL_CHANELS = """
select distinct name, id_group, type, technic
from groups
where technic=0
"""

INSERT_EVENT = """
insert into events (type_event, id_user, id_group, datetime, id_admin, hash, username_admin, username_user) values ('{type_event}', '{id_user}', '{id_group}', '{datetime}', '{id_admin}', '{hash}', '{username_admin}', '{username_user}')
"""

SELECT_EVENT_ID = """
select * from events where hash = '{hash}'
"""

SELECT_COUNT_EVENT_JOIN = """
select count(*) as count
from events
where type_event = 'member_joined' 
    and substr(datetime, 1, 10) = '{date}'
    and id_group = '{id_group}'
"""

SELECT_COUNT_EVENT_LEFT = """
select count(*) as count
from events
where type_event = 'member_left' 
    and substr(datetime, 1, 10) = '{date}'
    and id_group = '{id_group}'
"""

SELECT_USERNAME_JOIN = """
select distinct username_user
from events
where type_event = 'member_joined' 
    and substr(datetime, 1, 10) = '{date}'
    and id_group = '{id_group}'
"""

SELECT_USERNAME_LEFT = """
select distinct username_user
from events
where type_event = 'member_left' 
    and substr(datetime, 1, 10) = '{date}'
    and id_group = '{id_group}'
"""