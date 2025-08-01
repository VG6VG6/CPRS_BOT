import os
from tools import log
import sys
from src.Client.botUTILS import BOT
from src.Server.Users import USERS

def load_environment() -> None:
    with open("bin/.env", "r") as f:
        try:
            for line in f:
                key, val = line.split('=')
                os.environ[key] = val
        except:
            print("Fatal error. Error loading data from .env file.")


def main() -> None:
    # sys.stdout = open("bin/LOG.txt", 'a')
    load_environment()
    bot = BOT(os.environ["BOT_TOKEN"])
    bot.Polling()
# Users = USERS()
# Fields = Users.GetDefaultFields()
# Fields["Name"], Fields["Surname"], Fields["Patronymic"], Fields["role"] = "Владислав", "Голубов", "Александрович", "admin"
# Fields["tgId"] = "814497972"
# Users.Insert(Fields)
if __name__ == "__main__":
    main()