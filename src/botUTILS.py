import telebot

bot = None

def telebotInstal(TOKEN):
    global bot
    bot = telebot.TeleBot(TOKEN)

    return bot

def botSendMessage(message, text, keyboard = None):
    global bot

    if keyboard:
        bot.send_message(message.from_user.id, text, reply_markup=keyboard)
    else:
        bot.send_message(message.from_user.id, text)

def botSendMessageToAllUsers(message, Users):
    Inp = str(message.text)
    if Inp.startswith('/'):
        botSendMessage(message, "Отмена")
        return

    for user in Users.usersList:
        try:
            if user[4] not in Users.banList:
                bot.send_message(user[4], f"{Inp}")
        except:
            botSendMessage(message, f"Не удолось отправить сообщение для {user}")
    botSendMessage(message, f"Сообщения разосланы")

def botGetCastomeKeyboard(keys: list):
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for key in keys:
        button = telebot.types.KeyboardButton(text=key)
        keyboard.add(button)
    return keyboard

def botNextStepHendler(message, func, *args, **kwargs):
    bot.register_next_step_handler(message, func, *args, **kwargs)

def botPolling():
    bot.polling(none_stop=True)
    bot.infinity_polling()