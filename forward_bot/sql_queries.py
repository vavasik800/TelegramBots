CREATE_TABLE = """
create table groups_for_forward_bot
(
    id       integer not null
        constraint groups_pk
            primary key autoincrement,
    name     TEXT,
    id_group TEXT,
    type     TEXT,
    technic  BLOB default FALSE
);
"""
SELECT_IDS = """
select *
from forward_app_forwardmessagesgroup
where name_bot = "1"
"""



