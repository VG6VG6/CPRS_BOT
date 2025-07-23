import telebot
from telebot import types
from src.tools import log
import json
import os
from src.Server.Patients import PATIENTS
from src.Server.Users import USERS

def CommandDecorator(func):
    def wrapper(*args, **kwargs):
        res = func(*args, **kwargs)
        print("Check me pls.")
        return res
    return wrapper

class BOT:
    def __init__(self, TOKEN: str):
        try:
            self.bot = telebot.TeleBot(TOKEN)
            self._register_handlers()
        except:
            print("Error connection to telegram bot. Token is incorrect.")
            exit(1)
        self.Users = USERS()
        self.Patients = PATIENTS()

    def SendMessage(self, message: types.Message, text, keyboard = None):
        if keyboard:
            self.bot.send_message(message.from_user.id, text, reply_markup=keyboard)
        else:
            self.bot.send_message(message.from_user.id, text)

    @CommandDecorator
    def SendMessageToAllUsers(self, message: types.Message, UsersIds):
        Inp = str(message.text)

        for userId in UsersIds:
            try:
                self.bot.send_message(userId, f"{Inp}")
            except:
                self.SendMessage(message, f"Не удолось отправить сообщение для {userId}")
        self.SendMessage(message, f"Сообщения разосланы")

    def GetCustomKeyboard(self, keys: list = [["A", "B"], "C"]):
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        buttons = []
        for row in keys:
            # buttons_row = []
            # for elem in row:
            #     button = types.KeyboardButton(text=elem)
            #     buttons_row.append(button)
            keyboard.row(*row)
        return keyboard

    def NextStepHendler(self, message: types.Message, func, *args, **kwargs):
        self.bot.register_next_step_handler(message, func, *args, **kwargs)

    def Polling(self):
        while True:
            try:
                self.bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
                # self.bot.infinity_polling(long_polling_timeout=60)
            except KeyboardInterrupt:
                break
            except Exception as e:
                log(f"Polling ERROR: {e}")

    def CheckTgId(self, tg_id: str, role: str = "Any") -> bool:
        AllUsers = self.Users.GetDataBase()
        if role == "Any":
            return tg_id in [user["tgId"] for user in AllUsers]
        else:
            map = {user["tgId"]: user["role"] for user in AllUsers}
            if tg_id in map.keys():
                return map[tg_id] == role
            return False


    def _register_handlers(self):
        """Регистрация всех обработчиков сообщений"""

        @self.bot.message_handler(commands=['start'])
        def StartMessage(message: types.Message):
            with open("bin/Texts.json", 'r', encoding='utf-8') as f:
                texts = json.load(f)
            tgId = str(message.from_user.id)
            print(tgId)
            if self.CheckTgId(tgId, "admin"):
                self.SendMessage(message, texts['AdminStart'])
            elif self.CheckTgId(tgId):
                self.SendMessage(message, texts['WaitStart'])
            else:
                self.SendMessage(message, texts['FirstStart'])
                self.NextStepHendler(message, self.RegisterUser)

        @self.bot.message_handler(func=lambda msg: True)
        def handle_all_messages(message: types.Message):
            pass

    @CommandDecorator
    def RegisterUser(self, message: types.Message, UserRegisterData: dict = {}):
        if UserRegisterData:
            if message.text == "Да":
                fields = self.Users.GetDefaultFields()
                fields["Surname"], fields["Name"], fields["Patronymic"] = (
                    UserRegisterData["Surname"], UserRegisterData["Name"], UserRegisterData["Patronymic"])
                fields["tgId"] = str(message.from_user.id)
                fields["role"] = "New user"
                self.Users.Insert(fields)
            elif message.text == "Нет":
                self.NextStepHendler(message, self.RegisterUser)
        else:
            if message.text.count(' ') != 2:
                self.SendMessage(message, "Некорректный формат ввода. Введите ФИО.")
                self.NextStepHendler(message, self.RegisterUser)
            else:
                UserRegisterData["Surname"], UserRegisterData["Name"], UserRegisterData["Patronymic"] = message.text.split(' ')
                self.SendMessage(message, f'Фамилия: {UserRegisterData["Surname"]}\n'
                                               f'Имя: {UserRegisterData["Name"]}\n'
                                               f'Отчество: {UserRegisterData["Patronymic"]}\n'
                                          f"Верно?", self.GetCustomKeyboard([["Да", "Нет"]]))
                self.NextStepHendler(message, self.RegisterUser)




