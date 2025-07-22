import telebot
from telebot import types

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
        except:
            print("Error connection to telegram bot. Token is incorrect.")
            exit(1)

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
            buttons_row = []
            for elem in row:
                button = types.KeyboardButton(text=elem)
                buttons_row.append(button)
            buttons.append(buttons_row)
        keyboard.add(buttons)
        return keyboard

    def NextStepHendler(self, message: types.Message, func, *args, **kwargs):
        self.bot.register_next_step_handler(message, func, *args, **kwargs)

    def Polling(self):
        self.bot.polling(none_stop=True)
        self.bot.infinity_polling()