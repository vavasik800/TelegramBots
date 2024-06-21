from pyrogram import Client, types, filters

from dbEditor import SqlLiteEditor
import config, queries

editor = SqlLiteEditor(config.PATH_DB)
answer = editor.run(query=queries.SELECT_API_DATA, type='select')
print(answer)

API_ID = answer[0].get('api_id')
API_HASH = answer[0].get('api_hash')

client = Client('admin', api_id=config.API_ID, api_hash=config.API_HASH)

client.start()
client.stop()

