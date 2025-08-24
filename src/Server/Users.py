import src.Server.DB as DB
from src.Server.DB import log

class USERS(DB.DATA_BASE):

    def __init__(self):
        User_DB_Fields = {
        "id": "INTEGER PRIMARY KEY",
        "Name": "TEXT NOT NULL",
        "Surname": "TEXT NOT NULL",
        "Patronymic": "TEXT NOT NULL",
        "tgId": "TEXT NOT NULL",
        "role": "TEXT NOT NULL"
        }
        super().__init__("USERS", User_DB_Fields)
        # Default dictionary with all fields of Users data. It will be filled in DB class __init__ method
        self.DefaultFields = super().GetDefaultFields()


    def getUser(self, tgId: str) -> dict:
        return self.GetDataBase(f"tgId = {tgId}")

    def getRole(self, tgId: str):
        user = self.GetDataBase(f"tgId = {tgId}")
        if user:
            return user["role"]
        return None


