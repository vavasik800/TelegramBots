import config
from get_username import GetUsernameBot


def main():
    client = GetUsernameBot(config.API_ID, config.API_HASH)
    client.run()
    return


if __name__ == '__main__':
    main()
