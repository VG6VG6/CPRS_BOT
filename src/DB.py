import sqlite3

def Safty_DB_Decorator(func):
    def wrapper(*args, **kwargs):
        try:
            res = func()
            return res
        except sqlite3.Error as e:
            print(f"Ошибка выполнения функции {func.__name__}: {e}")
            return None
    return wrapper

class DATA_BASE:

    @Safty_DB_Decorator
    def __init__(self, DB_Name : str, DB_Field: dict = {"BaseField": "None"}) -> None:
        self.DB_Name = DB_Name
        self.DB_Field = DB_Field
        self.DB_Path = "bin/"+DB_Name+".db"
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

    @Safty_DB_Decorator
    def ShowDataBase(self, Condition : str = ""):
        connection = sqlite3.connect(self.DB_Path)
        cursor = connection.cursor()
        if Condition:
            cursor.execute(f"SELECT * FROM {self.DB_Name} WHERE {Condition}")
        else:
            cursor.execute(f"SELECT * FROM {self.DB_Name}")

        for line in cursor.fetchall():
            print(line)
        connection.close()

    def Insert(self, Fields_Data) -> bool:
        try:
            connection = sqlite3.connect(self.DB_Path)
            cursor = connection.cursor()

            connection.commit()
            connection.close()
            return True
        except sqlite3.Error as e:
            print(f"Ошибка при выполнении функции Insert({self.DB_Name}): {e}")
            return False