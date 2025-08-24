import re
from src.Client.botUTILS import BOT
from src.tools import validate_phone, validate_passport, validate_snils, validate_date, log, validate_fio
from telebot import types

# Список полей для регистрации пациента
PATIENT_REG_FIELDS = [
    ("Surname", "Фамилия", None),
    ("Name", "Имя", None),
    ("Patronymic", "Отчество", None),
    ("Birthday", "Дата рождения", None),
    ("Sex", "Пол", [["Мужской", "Женский"]]),
    ("Passport", "Паспорт", None),
    ("Phone", "Телефон", None),
    ("Snils", "СНИЛС", None),
    ("Name_of_the_medical_institution_from_where_it_was_sent", "Название ЛПУ откуда направлен", None),
    ("Surgical_treatment_for_CRF", "Хирургическое лечение по поводу ХПРС", [["Да", "Нет"]]),
    ("Noof_operation", "Количество операций", None),  # Автоматически 0, если выше 'Нет'
    ("Presence_of_aspirin_triad", "Наличие аспириновой триады", [["Да", "Нет"]]),
    ("Presence_of_bronchial_asthma", "Наличие бронхиальной астмы", [["Лёгкая", "Средняя", "Тяжёлая"], ["Нет"]]),
    ("Presence_of_other_T2_inflammations", "Наличие других Т2 воспалений (АД, ЭЭ, УЗП)", [["Да", "Нет"]]),
    ("Commission_date", "Дата комиссии", None),
    ("Results_of_the_commission", "Результаты комиссии", None),
    ("Initiation_date", "Дата инициации", None),
    ("Biological_status", "Биологический статус", [["Bio-native", "BEN", "DUP"], ["MEP", "OMA", "RES"]]),
    ("Therapy_status", "Статус терапии", None)
]

BotMain = BOT()

def start_registration(message: types.Message, step=0, patient_data=None):
    if patient_data is None:
        patient_data = {}
    if step >= len(PATIENT_REG_FIELDS):
        # Сохраняем в БД
        if BotMain.Patients.Insert(patient_data):
            BotMain.SendMessage(message, "Пациент успешно добавлен!")
            message.text = patient_data["Passport"]
            BotMain.FindPatientByField(message, "Passport")
        else:
            BotMain.SendMessage(message, "Произошла ошибка. Пациент не был добавлен.")
            log(f"ERROR PATIENT ADD!!! message:\n{message}\npatient_data:{patient_data}")
        return

    key, label, options = PATIENT_REG_FIELDS[step]

    # Логика пропуска количества операций
    if key == "Noof_operation" and patient_data.get("Surgical_treatment_for_CRF") == "Нет":
        patient_data[key] = "0"
        return start_registration(message, step + 1, patient_data)

    # Запрос данных
    if key in ("Name", "Surname", "Patronymic"):
        BotMain.SendMessage(message, f"Введите ФИО (Фамилия Имя Отчество):")
        BotMain.NextStepHendler(message, lambda msg: registration_step_handler(msg, step, patient_data))
        return

    keyboard = BotMain.GetCustomKeyboard(options)
    BotMain.SendMessage(message, f"Введите {label}:", keyboard)
    BotMain.NextStepHendler(message, lambda msg: registration_step_handler(msg, step, patient_data))

def registration_step_handler(message: types.Message, step, patient_data):
    key, label, options = PATIENT_REG_FIELDS[step]
    value = message.text.strip()

    # ✅ Валидация ФИО
    if key in ("Name", "Surname", "Patronymic"):
        if not validate_fio(value):
            BotMain.SendMessage(message, f"Некорректный формат ФИО. Попробуйте снова.")
            return start_registration(message, step, patient_data)
        Surname, Name, Patr = value.split(' ')
        patient_data["Surname"] = Surname
        patient_data["Name"] = Name
        patient_data["Patronymic"] = Patr
        return start_registration(message, step + 3, patient_data)

    # ✅ Валидация телефона
    if key == "Phone":
        normalized = validate_phone(value)
        if not normalized:
            BotMain.SendMessage(message, f"Некорректный номер телефона. Формат: +7XXXXXXXXXX или 8XXXXXXXXXX")
            return start_registration(message, step, patient_data)
        value = normalized

    # ✅ Валидация паспорта
    if key == "Passport":
        normalized = validate_passport(value)
        if not normalized:
            BotMain.SendMessage(message, f"Некорректный формат паспорта. Формат: XXXX XXXXXX")
            return start_registration(message, step, patient_data)
        value = normalized

    # ✅ Валидация СНИЛС
    if key == "Snils":
        normalized = validate_snils(value)
        if not normalized:
            BotMain.SendMessage(message, f"Некорректный формат СНИЛС. Формат: XXX-XXX-XXX XX")
            return start_registration(message, step, patient_data)
        value = normalized

    # ✅ Валидация дат
    if key in ("Commission_date", "Initiation_date"):
        normalized = validate_date(value)
        if not normalized:
            BotMain.SendMessage(message, f"Некорректная дата. Формат: DD.MM.YYYY")
            return start_registration(message, step, patient_data)
        value = normalized

    # Записываем и двигаемся дальше
    patient_data[key] = value
    start_registration(message, step + 1, patient_data)
