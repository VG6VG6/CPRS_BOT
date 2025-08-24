from src.Client.botUTILS import BOT
from src.tools import log, validate_date
from telebot import types

HALFYEAR_ANALYSES_FIELDS = [
    ("IGKS", "ИГКС", [["Да", "Нет"]]),
    ("System_GK", "Системные ГК", [["Да", "Нет"]]),
    ("Eosinophils", "Количество эозинофилов, ед/мкол", None),
    ("IgE", "Общий IgE, МЕ/мл2", None),
    ("SNOT22", "SNOT-22, баллы", [["0-29", "30-69", "70-100"]]),
    ("VAS", "ВАШ, баллы", [["0-3", "4-6", "7-10"]]),
    ("Lund_Mackay", "Шкала Лунд-Маккея, баллы (0-24)", None),
    ("NSP", "Назальная обструкция NSP", ["0123", "45678"]),
    ("Smell_loss", "Снижение обоняния", [["35-40", "31-34", "26-30"], ["19-25", "<18"]]),
    ("Doctor_comment", "Комментарий врача", None),
    ("Date", "Дата", None)
]

BotMain = BOT()

def start_halfyear_survey(message: types.Message, patient_id, step=0, survey_data=None):
    if survey_data is None:
        survey_data = {"patient_id": patient_id}
    if step >= len(HALFYEAR_ANALYSES_FIELDS):
        if BotMain.HalfYearAnalyses.Insert(survey_data):
            BotMain.SendMessage(message, "Анкета завершена! Данные сохранены.")
            user = BotMain.Users.getUser(str(message.from_user.id))
            if user:
                log(f"{user} ADD NEW HALF YEAR SURVEY: {survey_data} IN PATIENT {patient_id}: {BotMain.Patients.GetDataBase(f'id = {patient_id}')}")
            else:
                log(f"NO NAME ADD NEW HALF YEAR SURVEY: {survey_data} IN PATIENT {patient_id}: {BotMain.Patients.GetDataBase(f'id = {patient_id}')}")
        else:
            BotMain.SendMessage(message, "Произошла ошибка. Пациент не был добавлен.")
            log(f"ERROR PATIENT ADD!!! message:\n{message}\nsurvey_data:{survey_data}")
        message.text = str(patient_id)
        BotMain.FindPatientByField(message, "id")
        return

    key, label, options = HALFYEAR_ANALYSES_FIELDS[step]
    keyboard = BotMain.GetCustomKeyboard(options)
    BotMain.SendMessage(message, f"{label}:", keyboard)
    BotMain.NextStepHendler(message, lambda msg: halfyear_survey_step_handler(msg, patient_id, step, survey_data))

def halfyear_survey_step_handler(message: types.Message, patient_id, step, survey_data):
    key, label, options = HALFYEAR_ANALYSES_FIELDS[step]
    value = message.text.strip()

    # Валидируем числовые поля
    if key in ("Eosinophils", "IgE", "Lund_Mackay"):
        if not value.isdigit():
            BotMain.SendMessage(message, f"⚠️ Введите числовое значение для поля «{label}».")
            return start_halfyear_survey(message, patient_id, step, survey_data)

    # Валидируем дату
    if key == "Date":
        if not validate_date(value):
            BotMain.SendMessage(message, f"⚠️ Неверный формат даты. Используйте формат: дд.мм.гггг")
            return start_halfyear_survey(message, patient_id, step, survey_data)

    survey_data[key] = value
    start_halfyear_survey(message, patient_id, step + 1, survey_data)

def halftear_edit_choose(message: types.Message, halfYearAnalyses):
    if message.text == "Отмена":
        message.text = str(halfYearAnalyses[0]["patient_id"])
        BotMain.FindPatientByField(message, "id")
        return
    if not message.text.isdigit():
        BotMain.SendMessage(message, f"{message.text} не является числом. Попробуйте снова")
        BotMain.NextStepHendler(message, halftear_edit_choose, halfYearAnalyses)
        return
    ControlNumber = int(message.text)
    if 0 < ControlNumber <= len(halfYearAnalyses):
        halftear_edit_filed(message, halfYearAnalyses[ControlNumber-1])
    else:
        BotMain.SendMessage(message, f"Некорректное число. Попробуйте снова")
        BotMain.NextStepHendler(message, halftear_edit_choose, halfYearAnalyses)

def halftear_edit_filed(message: types.Message, halfYearAnalyses, field=None):
    if message.text == "Отмена":
        message.text = str(halfYearAnalyses[0]["patient_id"])
        BotMain.FindPatientByField(message, "id")
    if not halfYearAnalyses:
        BotMain.SendMessage(message, "Ошибка обновления. Не удалось найти данных для изменения.")
        log("Ошибка обновления. Не удалось найти данны для изменения.")
        return
    if halfYearAnalyses.get("id", "False") == "False":
        BotMain.SendMessage(message, "Ошибка обновления. Не удалось найти id данных для изменения.")
        log("Ошибка обновления. Не удалось найти id данны для изменения.")
        return

    if not field:
        if message.text in [_[1] for _ in HALFYEAR_ANALYSES_FIELDS]:
            field = message.text
            halftear_edit_filed(message, halfYearAnalyses, field)
        else:
            keyboard = BotMain.GetCustomKeyboard([[_[1]] for _ in HALFYEAR_ANALYSES_FIELDS])
            BotMain.SendMessage(message, "Выберете поле для изменения:", keyboard=keyboard)
            BotMain.NextStepHendler(message, halftear_edit_filed, halfYearAnalyses, field)
        return
    elif field not in [_[1] for _ in HALFYEAR_ANALYSES_FIELDS]:
        keyboard = BotMain.GetCustomKeyboard([[_[1] for _ in HALFYEAR_ANALYSES_FIELDS]])
        BotMain.SendMessage(message, "Выберете корректное поле для изменения. Воспользуйтесь специальной клавиатурой.", keyboard=keyboard)
        BotMain.NextStepHendler(message, halftear_edit_filed, halfYearAnalyses, field)
        return
    else:
        for key, label, btn in HALFYEAR_ANALYSES_FIELDS:
            if label == field:
                keyboard = BotMain.GetCustomKeyboard(btn)
                FieldKey = key
                break
        else:
            keyboard = BotMain.GetCustomKeyboard()
            FieldKey = ""
        BotMain.SendMessage(message, f"Введите новое значение для поля {field}",
                            keyboard=keyboard)
        BotMain.NextStepHendler(message, _halfyear_edit, field, FieldKey, halfYearAnalyses)


def _halfyear_edit(message: types.Message, field, fieldKey, halfYearAnalyses):
    fieldVal = message.text
    if fieldVal == "Отмена" or fieldVal.startswith('/'):
        BotMain.SendMessage(message, "Операция завершена.")
        return
    analises_id = halfYearAnalyses['id']
    if BotMain.HalfYearAnalyses.Update({fieldKey: fieldVal}, f"id='{analises_id}'"):
        BotMain.SendMessage(message, "✅ Данные успешно обновлены.")
        action = "UPDATE"
    else:
        BotMain.SendMessage(message, "❌ Не удалось обновить данные.")
        action = "TRY TO UPDATE"
    user = BotMain.Users.getUser(str(message.from_user.id))
    if user:
        log(f"{user} {action} NEW HALF YEAR SURVEY: {halfYearAnalyses}: {BotMain.HalfYearAnalyses.GetDataBase(f'id = {analises_id}')}")
    else:
        log(f"NO NAME {action} NEW HALF YEAR SURVEY: {halfYearAnalyses}: {BotMain.HalfYearAnalyses.GetDataBase(f'id = {analises_id}')}")
    patient_id = halfYearAnalyses['patient_id']
    message.text = str(patient_id)
    BotMain.FindPatientByField(message, "id")



