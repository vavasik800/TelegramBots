# Forward_bot_telethon
***
This **__telegram-userbot__** forwards messages from some telegram-channels to other telegram-channels. 
The bot begin creates table to DataBase (format SqLite) for storing telegram-channels. 

### Technologies 

* Python
* SQLite
* python-modules: Telethon==1.36.0, APScheduler==3.10.4, loguru==0.7.2.

### Modules

* #### dbEditor.py

  This module has class SqlLiteEditor, which work with database and executes sql-requests.
This class contains one public method __**run(query, type)**__.
    
  ###### Example:
  ```python
  path = 'sql_db.sqlite3'
  query = "select * from table_1"
  db_con = SqlLiteEditor(path)
  result = db_con.run(query, type="select")
  ```
* #### sql_queries.py

  This module has sql-queries for work with bot.
  * CREATE_TABLE - query for create table with telegram-channels.
  * SELECT_IDS - query for get all channels.

* #### config.py 
  This file has configuration parameters for userbot.

  * API_ID, API_HASH - parameters for work userbot;
  * DB_PATH - path for file database;
  * COLUMN_ID_CHANEL, COLUMN_NAME_CHANEL, COLUMN_TECH_CHANEL - column's name in database.

* #### forward_bot.py
  
  The engine of the bot. The bot monitors the database every 2 minutes to add or remove new 
channels for monitoring. After a new message appears in the channels, it forwards them to all technical 
channels. Listening database with help python-module __**APScheduler**__.

  ###### Example:
  ```python
  import config
  
  bot = SendMessageChanelBot(config.API_ID, config.API_HASH)
  bot.run()
  ```

* #### run_bot.py
  The file runs bot.