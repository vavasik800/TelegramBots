import config
from forward_bot import SendMessageChanelBot

if __name__ == "__main__":
    bot = SendMessageChanelBot(config.API_ID, config.API_HASH)
    bot.run()
