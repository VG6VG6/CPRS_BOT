import telebot
from telebot import types
from src.tools import log
import json
import os
from src.Server.Patients import PATIENTS
from src.Server.Users import USERS
from src.Server.Analyses import ANALYSES
import re

def CommandDecorator(func):
    def wrapper(self, message, *args, **kwargs):
        if hasattr(message, 'text') and isinstance(message.text, str) and message.text.startswith('/'):
            # Передаём сообщение обратно в Telebot для обработки как команды
            self.bot.process_new_updates([message])
            return
        return func(self, message, *args, **kwargs)
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
        self.Analyses = ANALYSES()

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

    def has_patient_access(self, tg_id: str) -> bool:
        # Проверка, может ли пользователь работать с пациентами
        all_users = self.Users.GetDataBase(f'tgId = "{tg_id}"')
        if not all_users:
            return False
        role = all_users[0].get("role", "user")
        return role in ["admin", "doctor"]

    def validate_fio(self, fio: str) -> bool:
        # ФИО: три слова, только буквы, первая буква заглавная
        parts = fio.strip().split()
        if len(parts) != 3:
            return False
        return all(re.match(r'^[А-ЯЁA-Z][а-яёa-z]+$', part) for part in parts)

    def _register_handlers(self):
        """Регистрация всех обработчиков сообщений"""

        @self.bot.message_handler(commands=['start'])
        def StartMessage(message: types.Message):
            with open("bin/Texts.json", 'r', encoding='utf-8') as f:
                texts = json.load(f)
            tgId = str(message.from_user.id)
            user = None
            for u in self.Users.GetDataBase():
                if u["tgId"] == tgId:
                    user = u
                    break
            if user:
                role = user.get("role", "user")
                if role == "admin":
                    self.SendMessage(message, texts['AdminStart'])
                elif role == "doctor":
                    self.SendMessage(message, texts['DoctorStart'])
                elif role == "user":
                    self.SendMessage(message, texts['UserStart'])
                else:
                    self.SendMessage(message, texts['WaitStart'])
            else:
                self.SendMessage(message, texts['FirstStart'])
                self.NextStepHendler(message, self.RegisterUser)

        @self.bot.message_handler(commands=['changerole'])
        def ChangeRoleCommand(message: types.Message):
            tgId = str(message.from_user.id)
            if not self.CheckTgId(tgId, "admin"):
                self.SendMessage(message, "Нет прав для выполнения этой команды.")
                return
            keyboard = self.GetCustomKeyboard([["По tgId", "По ФИО"]])
            self.SendMessage(message, "Выберите способ поиска пользователя:", keyboard)
            self.NextStepHendler(message, self.ChangeRoleChooseMethod)

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
            if not self.validate_fio(message.text):
                self.SendMessage(message, "Некорректный формат ввода. Введите ФИО (три слова, первая буква заглавная, только буквы).")
                self.NextStepHendler(message, self.RegisterUser)
            else:
                UserRegisterData["Surname"], UserRegisterData["Name"], UserRegisterData["Patronymic"] = message.text.split(' ')
                self.SendMessage(message, f'Фамилия: {UserRegisterData["Surname"]}\n'
                                               f'Имя: {UserRegisterData["Name"]}\n'
                                               f'Отчество: {UserRegisterData["Patronymic"]}\n'
                                          f"Верно?", self.GetCustomKeyboard([["Да", "Нет"]]))
                self.NextStepHendler(message, self.RegisterUser)

    def ChangeRoleChooseMethod(self, message: types.Message):
        if message.text == "По tgId":
            self.SendMessage(message, "Введите tgId пользователя, которому хотите изменить роль:")
            self.NextStepHendler(message, self.ChangeRoleStep2)
        elif message.text == "По ФИО":
            self.SendMessage(message, "Введите ФИО пользователя (три слова через пробел):")
            self.NextStepHendler(message, self.ChangeRoleStepFIO)
        else:
            self.SendMessage(message, "Пожалуйста, выберите один из предложенных вариантов.")
            self.NextStepHendler(message, self.ChangeRoleChooseMethod)

    def ChangeRoleStepFIO(self, message: types.Message):
        fio = message.text.strip()
        if not self.validate_fio(fio):
            self.SendMessage(message, "Некорректный формат ФИО. Введите ФИО (три слова, первая буква заглавная, только буквы).")
            self.NextStepHendler(message, self.ChangeRoleStepFIO)
            return
        surname, name, patronymic = fio.split()
        users = self.Users.GetDataBase(f'Surname = "{surname}" AND Name = "{name}" AND Patronymic = "{patronymic}"')
        if not users:
            self.SendMessage(message, "Пользователь с таким ФИО не найден. Попробуйте снова.")
            self.NextStepHendler(message, self.ChangeRoleStepFIO)
            return
        if len(users) > 1:
            self.SendMessage(message, "Найдено несколько пользователей с таким ФИО. Пожалуйста, используйте tgId.")
            return
        user_tgId = users[0]["tgId"]
        self.SendMessage(message, "Введите новую роль для пользователя (например, user, admin):")
        self.NextStepHendler(message, self.ChangeRoleStep3, user_tgId)

    def ChangeRoleStep2(self, message: types.Message):
        user_tgId = message.text.strip()
        if not self.Users.GetDataBase(f'tgId = "{user_tgId}"'):
            self.SendMessage(message, "Пользователь с таким tgId не найден. Попробуйте снова.")
            self.NextStepHendler(message, self.ChangeRoleStep2)
            return
        self.SendMessage(message, "Введите новую роль для пользователя (например, user, admin):")
        self.NextStepHendler(message, self.ChangeRoleStep3, user_tgId)

    def ChangeRoleStep3(self, message: types.Message, user_tgId):
        new_role = message.text.strip()
        if new_role not in ["user", "doctor", "admin"]:
            self.SendMessage(message, "Некорректная роль. Доступные роли: user, doctor, admin.")
            self.NextStepHendler(message, self.ChangeRoleStep3, user_tgId)
            return
        users = self.Users.GetDataBase(f'tgId = "{user_tgId}"')
        if not users:
            self.SendMessage(message, "Ошибка: пользователь не найден.")
            return
        user = users[0]
        user['role'] = new_role
        self.Users.Update({'role': new_role}, f'tgId = "{user_tgId}"')
        self.SendMessage(message, f"Роль пользователя {user_tgId} изменена на {new_role}.")




