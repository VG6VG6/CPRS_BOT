import sqlite3
from src.tools import log

def Safty_DB_Decorator(func):
    def wrapper(*args, **kwargs):
        try:
            res = func(*args, **kwargs)
            return res
        except sqlite3.Error as e:
            log(f"Ошибка выполнения функции {func.__name__}: {e}")
            return None
    return wrapper

class DATA_BASE:

    @Safty_DB_Decorator
    def __init__(self, DB_Name : str, DB_Field: dict = {"BaseField": "None"}) -> None:
        self.DB_Name = DB_Name
        self.DB_Field = DB_Field
        self.DB_Path = "bin/"+DB_Name+".db"
        self.DefaultFields: dict = {}
        connection = sqlite3.connect(self.DB_Path)
        cursor = connection.cursor()

        # make correct sql command
        Fields = ""
        for FieladName, FieldDescription in DB_Field.items():
            Fields += f"{FieladName} {FieldDescription},\n"

        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {DB_Name} (
            {Fields[:-2]}
            )
            """)
        connection.commit()
        connection.close()

    def GetDefaultFields(self) -> dict:
        if self.DefaultFields:
            return self.DefaultFields
        values = []
        for key in list(self.DB_Field.keys())[1:]:
            if "INT" in self.DB_Field[key]:
                values.append(-1)
            elif "TEXT" in self.DB_Field[key]:
                values.append("None")
            else:
                log(f"Error. Unknown type of DB field. DB: {self.DB_Name}. Field: \"{key}: {self.DB_Field[key]}\"")
        self.DefaultFields = dict(zip(list(self.DB_Field.keys())[1:], values))

        return self.DefaultFields

    @Safty_DB_Decorator
    def GetDataBase(self, Condition: str = "") -> list:
        connection = sqlite3.connect(self.DB_Path)
        cursor = connection.cursor()
        if Condition:
            cursor.execute(f"SELECT * FROM {self.DB_Name} WHERE {Condition}")
        else:
            cursor.execute(f"SELECT * FROM {self.DB_Name}")
        Data = cursor.fetchall()
        NiceData = []
        fields = self.GetDefaultFields()
        Keys = list(fields.keys())
        for line in Data:
            NiceData.append(fields)
            for i in range(len(line) - 1):
                NiceData[-1][Keys[i]] = line[i+1]
        return NiceData

    def ShowDataBase(self, Condition : str = ""):
        for line in self.GetDataBase():
            log(line)

    @Safty_DB_Decorator
    def Insert(self, Fields_Data: dict) -> bool:
        if self.GetDefaultFields().keys() != Fields_Data.keys():
            print("Incorrect fields data. Fields keys don`t match. ")
            return False
        try:
            connection = sqlite3.connect(self.DB_Path)
            cursor = connection.cursor()

            fields = ", ".join(list(Fields_Data.keys()))
            val = "'" + "', '".join(list(Fields_Data.values())) + "'"

            cursor.execute(f"""INSERT INTO {self.DB_Name} ({fields}) VALUES ({val})""")

            connection.commit()
            connection.close()
            return True
        except sqlite3.Error as e:
            log(f"Ошибка при выполнении функции Insert({self.DB_Name}): {e}")
            return False