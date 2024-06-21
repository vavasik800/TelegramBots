# TelegramBots
***
A set of telegram bots for automating processes.

* ### System_bot

  Telegram ___**userbot**___ is designed to read service information from telegram channels 
and forward it to a special technical channel. The bot sends information 
about adding, deleting and other technical messages. 
It also counts statistics on all added and deleted users per day. 

  * Use python module **___pyrogram___**;
  * DB: **___SQLite___**.

###### Example messages:
    #НОВЫЙ_УЧАСТНИК
    1. Пользователя добавил - @admin [111111];
    2. Новый пользователь - @new_user [2222222];
    3. Группа: test_group [-100001115];
    4. Дата события: 01.01.2020;
    5. Кто: #ID111111;
    6. Кого: #ID2222222;
    7. Куда: #ID100001115;
    8. #100001115111111;
    9. #1000011152222222;

    #СТАТИСТИКА
    1. Группа: test_group [100001115];
    2. Дата: 01.01.2020;
    3. Добавилось: 10 человек:
        ... (list new users) ... 
    4. Вышло: 2 человек:
       ... (list old users) ... 
    5. Прирост/убыль: 8.

* ### Get_username_bot

  Telegram user is a bot that checks whether the
specified phone number is visible in the telegram when adding it to
contacts. Request can have one phone number or list phones.

  * Use python module **___pyrogram___**;
  * DB: **___SQLite___**.

* ### Forward_bot
  The telegram __**userbot**__ forwards messages from channels to 
other channels specified by the user.

  * Use python module **___pyrogram___**;
  * DB: **___SQLite___**.

* ### Forward_bot_telethon
  The telegram __**userbot**__ forwards messages from channels to 
other channels specified by the user, but use library __telethon__.

  * Use python module **___telethon___**;
  * DB: **___SQLite___**.