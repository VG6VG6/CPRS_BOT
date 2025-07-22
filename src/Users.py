import DB

class USERS(DB.DATA_BASE):

    def __init__(self):
        User_DB_Fields = {
        "id": "INTEGER PRIMARY KEY",
        "Name": "TEXT NOT NULL",
        "Surname": "TEXT NOT NULL",
        "Patronymic": "TEXT NOT NULL",
        "tgId": "INT NOT NULL"
        }
        super().__init__("USERS", User_DB_Fields)



