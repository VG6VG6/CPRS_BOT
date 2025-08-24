import telebot
from telebot import types
from src.tools import log, validate_fio, Singleton, validate_passport, validate_snils
import json
from src.Server.Patients import PATIENTS
from src.Server.Users import USERS
from src.Server.Analyses import ANALYSES
from src.Server.HalfyearAnalyses import HALF_YEAR_ANALYSES

def CommandDecorator(func):
    def wrapper(self, message, *args, **kwargs):
        if hasattr(message, 'text') and isinstance(message.text, str) and message.text.startswith('/'):
            # Найти и вызвать нужный handler вручную
            command = message.text.split()[0][1:]
            for handler in self.bot.message_handlers:
                if handler['filters']['commands'] and command in handler['filters']['commands']:
                    return handler['function'](message)
            return
        return func(self, message, *args, **kwargs)
    return wrapper

def Admin(func):
    def wrapper(self, message, *args, **kwargs):
        if not self.CheckTgId(str(message.from_user.id), "admin"):
            self.SendMessage(message, "Нет прав для выполнения этой команды.")
            return
        return func(self, message, *args, **kwargs)
    return wrapper

class BOT(Singleton):
    _initialized = False
    AllRoles = ["user", "doctor", "admin"]
    ExcelPath = "out/test.xlsx"

    def __init__(self, TOKEN: str = ""):
        if self._initialized:
            return
        print("Bot class initialize.")
        self._initialized = True
        try:
            self.bot = telebot.TeleBot(TOKEN)
            self._register_handlers()
        except:
            print("Error connection to telegram bot. Token is incorrect.")
            exit(1)
        self.Users = USERS()
        self.Patients = PATIENTS()
        self.Analyses = ANALYSES()
        self.HalfYearAnalyses = HALF_YEAR_ANALYSES()

    def send_long_message(self, chat_id, text, max_length=4096):
        if len(text) <= max_length:
            self.bot.send_message(chat_id, text)
            return

        parts = []
        while text:
            if len(text) > max_length:
                split_pos = text.rfind('\n', 0, max_length)
                if split_pos == -1:
                    split_pos = text.rfind(' ', 0, max_length)
                if split_pos == -1:
                    split_pos = max_length

                parts.append(text[:split_pos])
                text = text[split_pos:].lstrip()
            else:
                parts.append(text)
                break

        for part in parts:
            self.bot.send_message(chat_id, part)

    def SendMessage(self, message: types.Message, text, keyboard = None, parse_mode=None):
        if keyboard and parse_mode:
            self.bot.send_message(message.from_user.id, text, reply_markup=keyboard, parse_mode=parse_mode)
        elif keyboard:
            self.bot.send_message(message.from_user.id, text, reply_markup=keyboard)
        elif parse_mode:
            self.bot.send_message(message.from_user.id, text, parse_mode=parse_mode)
        else:
            if len(text) > 4096:
                self.send_long_message(message.from_user.id, text)
            else:
                self.bot.send_message(message.from_user.id, text)
        # log(f"MESSAGE TO {message.from_user.username, message.from_user.first_name, message.from_user.last_name, message.from_user.id}:\n{text}")

    @CommandDecorator
    def SendMessageToAllUsers(self, message: types.Message, UsersIds):
        Inp = str(message.text)

        for userId in UsersIds:
            try:
                self.bot.send_message(userId, f"{Inp}")
            except:
                self.SendMessage(message, f"Не удолось отправить сообщение для {userId}")
        self.SendMessage(message, f"Сообщения разосланы")

    def GetCustomKeyboard(self, keys: list[list] = None):
        if not keys:
            return types.ReplyKeyboardRemove()

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for row in keys:
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
                tb = e.__traceback__
                while tb.tb_next:
                    tb = tb.tb_next
                filename = tb.tb_frame.f_code.co_filename
                line_no = tb.tb_lineno
                log(f"Polling ERROR in file {filename} string {tb.tb_lineno}: {e}")

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
            if not self.CheckTgId(str(message.from_user.id), "admin"):
                self.SendMessage(message, "Нет прав для выполнения этой команды.")
                return
            keyboard = self.GetCustomKeyboard([["По tgId", "По ФИО"]])

            AllUsers = ""
            UsersList = self.Users.GetDataBase()
            for id, user in enumerate(UsersList):
                AllUsers += f"{id}) {' '.join(map(str, user.values()))}"
                if id + 1 < len(UsersList):
                    AllUsers += '\n'

            self.SendMessage(message, AllUsers)
            self.SendMessage(message, "Выберите способ поиска пользователя:", keyboard)
            self.NextStepHendler(message, self.ChangeRoleChooseMethod)

        @self.bot.message_handler(commands=['newpatient'])
        def NewPatientCommand(message: types.Message):
            from src.Client.PatientReg import start_registration

            tgId = str(message.from_user.id)
            if not self.has_patient_access(tgId):
                self.SendMessage(message, "Нет прав для добавления пациентов.")
                return
            self.SendMessage(message, f"Добавление нового пациента.")
            start_registration(message)

        @self.bot.message_handler(commands=['findpatient'])
        def FindPatientCommand(message: types.Message):
            tgId = str(message.from_user.id)
            if not self.has_patient_access(tgId):
                self.SendMessage(message, "Нет прав для поиска пациентов.")
                return
            keyboard = self.GetCustomKeyboard([["ФИО", "id"], ["Паспорт", "СНИЛС"]])
            self.SendMessage(message, "По какому параметру искать пациента?", keyboard)
            self.NextStepHendler(message, self.FindPatientChooseField)

        @self.bot.message_handler(commands=['list'])
        def ListPatientsCommand(message: types.Message):
            tgId = str(message.from_user.id)
            if not self.has_patient_access(tgId):
                self.SendMessage(message, "Нет прав для просмотра списка пациентов.")
                return
            patients = self.Patients.GetDataBase()
            if not patients:
                self.SendMessage(message, "Пациентов не найдено.")
                return
            msg = "Список пациентов:\n"
            tab = ' ' * 5
            for p in patients:
                msg += f"id: {p.get('id', '-')}) {p.get('Surname', '-')} {p.get('Name', '-')} {p.get('Patronymic', '-')}\n"
                # msg += f"{tab}СНИЛС: {p.get('Snils', '-')}\n"
                # msg += f"{tab}Паспорт: {p.get('Passport', '-')}\n"
                # msg += f"{tab}Телефон: {p.get('Phone', '-')}\n"
            self.SendMessage(message, msg)

        @self.bot.message_handler(commands=['help'])
        def HelpCommand(message: types.Message):
            with open("bin/Texts.json", 'r', encoding='utf-8') as f:
                texts = json.load(f)
            self.bot.send_message(message.from_user.id, texts['Help'], parse_mode='HTML')

        @self.bot.message_handler(commands=['createNewExcelFile'])
        def CreateNewExcelFile(message: types.Message):
            from src.Client.ExcelCreator import ExcelExport

            if not self.CheckTgId(str(message.from_user.id), "admin"):
                self.SendMessage(message, "Нет прав для выполнения этой команды.")
                return

            ExcelExport(self.ExcelPath)
            self.SendMessage(message, "Отчёт сгенерирован.\n /getExcelFile - получить отчёт")

        @self.bot.message_handler(commands=['getExcelFile'])
        def GetExcelFile(message: types.Message):

            if not self.CheckTgId(str(message.from_user.id), "admin"):
                self.SendMessage(message, "Нет прав для выполнения этой команды.")
                return

            with open(self.ExcelPath, "rb") as file:
                self.bot.send_document(message.chat.id, file, caption="📄 Ваш отчет")


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
                log(f"был зарегистрирован новый пользователь:\n{fields}\n{message.from_user}")
            elif message.text == "Нет":
                self.NextStepHendler(message, self.RegisterUser)
        else:
            if not validate_fio(message.text):
                self.SendMessage(message,
                                 "Некорректный формат ввода. Введите ФИО (три слова, первая буква заглавная, только буквы).")
                self.NextStepHendler(message, self.RegisterUser)
            else:
                UserRegisterData["Surname"], UserRegisterData["Name"], UserRegisterData[
                    "Patronymic"] = message.text.split(' ')
                self.SendMessage(message, f'Фамилия: {UserRegisterData["Surname"]}\n'
                                          f'Имя: {UserRegisterData["Name"]}\n'
                                          f'Отчество: {UserRegisterData["Patronymic"]}\n'
                                          f"Верно?", self.self.GetCustomKeyboard([["Да", "Нет"]]))
                self.NextStepHendler(message, self.RegisterUser)

    @CommandDecorator
    def ChangeRoleChooseMethod(self, message: types.Message):
        if message.text == "По tgId":
            self.SendMessage(message, "Введите tgId пользователя, которому хотите изменить роль:", self.GetCustomKeyboard())
            self.NextStepHendler(message, self.ChangeRoleStep2)
        elif message.text == "По ФИО":
            self.SendMessage(message, "Введите ФИО пользователя (три слова через пробел):", self.GetCustomKeyboard())
            self.NextStepHendler(message, self.ChangeRoleStepFIO)
        else:
            self.SendMessage(message, "Пожалуйста, выберите один из предложенных вариантов.")
            self.NextStepHendler(message, self.ChangeRoleChooseMethod)

    @CommandDecorator
    def ChangeRoleStepFIO(self, message: types.Message):
        fio = message.text.strip()
        if not validate_fio(fio):
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

    @CommandDecorator
    def ChangeRoleStep2(self, message: types.Message):
        user_tgId = message.text.strip()
        if not self.Users.GetDataBase(f'tgId = "{user_tgId}"'):
            self.SendMessage(message, "Пользователь с таким tgId не найден. Попробуйте снова.")
            self.NextStepHendler(message, self.ChangeRoleStep2)
            return
        self.SendMessage(message, f"Введите новую роль для пользователя ({', '.join(self.AllRoles)}):")
        self.NextStepHendler(message, self.ChangeRoleStep3, user_tgId)

    @CommandDecorator
    def ChangeRoleStep3(self, message: types.Message, user_tgId):
        new_role = message.text.strip()
        if new_role not in self.AllRoles:
            self.SendMessage(message, "Некорректная роль. Доступные роли: user, doctor, admin.")
            self.NextStepHendler(message, self.ChangeRoleStep3, user_tgId)
            return
        users = self.Users.GetDataBase(f'tgId = "{user_tgId}"')
        if not users:
            self.SendMessage(message, "Ошибка: пользователь не найден.")
            return
        user = users[0]
        self.Users.Update({'role': new_role}, f'tgId = "{user_tgId}"')
        self.SendMessage(message, f"Роль пользователя {user_tgId} изменена на {new_role}.")
        AdminUser = self.Users.getUser(str(message.from_user.id))
        if AdminUser:
            log(f"{AdminUser} CHANGE: {user} ROLE TO {new_role}")
        else:
            log(f"Uncommon user CHANGE {user} ROLE TO {new_role}")

    @CommandDecorator
    def NewPatientStep(self, message: types.Message, field_idx: int, patient_data: dict):
        field_key, field_label = self.Patients.FIELDS[field_idx]
        patient_data[field_key] = message.text.strip()
        if field_idx + 1 < len(self.Patients.FIELDS):
            next_field_key, next_field_label = self.Patients.FIELDS[field_idx + 1]
            self.SendMessage(message, f"Введите {next_field_label}:")
            self.NextStepHendler(message, self.NewPatientStep, field_idx + 1, patient_data)
        else:
            # Все поля собраны, записываем в БД
            if self.Patients.Insert(patient_data):
                self.SendMessage(message, "Пациент успешно добавлен!")
                user = self.Users.getUser(str(message.from_user.id))
                if user:
                    log(f"{user} ADD NEW PATIENT: {patient_data}")
                else:
                    log("Uncommon user add patient!!!")
            else:
                self.SendMessage(message, "Произошла ошибка. Пациент не был добавлен.")
                log(f"ERROR PATIENT ADD!!! message:\n{message}\npatient_data:{patient_data}")

    @CommandDecorator
    def FindPatientChooseField(self, message: types.Message):
        field_map = {
            "ФИО": "fio",
            "id": "id",
            "Паспорт": "Passport",
            "СНИЛС": "Snils"
        }
        field = field_map.get(message.text)
        if not field:
            self.SendMessage(message, "Пожалуйста, выберите один из предложенных вариантов.")
            self.NextStepHendler(message, self.FindPatientChooseField)
            return
        if field == "fio":
            self.SendMessage(message, "Введите ФИО (три слова через пробел):")
            self.NextStepHendler(message, self.FindPatientByFIO)
        else:
            self.SendMessage(message, f"Введите значение для поиска по {message.text}:")
            self.NextStepHendler(message, self.FindPatientByField, field)

    @CommandDecorator
    def FindPatientByFIO(self, message: types.Message):
        fio = message.text.strip()
        if not validate_fio(fio):
            self.SendMessage(message, "Некорректный формат ФИО. Введите ФИО (три слова, первая буква заглавная, только буквы).")
            self.NextStepHendler(message, self.FindPatientByFIO)
            return
        surname, name, patronymic = fio.split()
        patients = self.Patients.GetDataBase(f'Surname = "{surname}" AND Name = "{name}" AND Patronymic = "{patronymic}"')
        self._show_patients_search_result(message, patients)

    @CommandDecorator
    def FindPatientByField(self, message: types.Message, field):
        value = message.text.strip()
        if field == "Passport":
            value = validate_passport(value)
        elif field == "Snils":
            value = validate_snils(value)
        if value:
            patients = self.Patients.GetDataBase(f'{field} = "{value}"')
            self._show_patients_search_result(message, patients)
        else:
            self.SendMessage(message, f"Некорректный формат {field}. Попробуйте снова")
            self.NextStepHendler(message, self.FindPatientByField, field)

    def _show_patients_search_result(self, message, patients):
        if not patients:
            self.SendMessage(message, "Пациент не найден.")
            return

        for idx, patient in enumerate(patients):
            # Patient data
            info = f"Пациент №{patient.get('id', 'Error')}\n"
            for key, label in self.Patients.FIELDS:
                info += f"{label}: {patient.get(key, '-') }\n"

            # Data before therapy
            from src.Client.halfyear_survey import HALFYEAR_ANALYSES_FIELDS
            BeforeTherapyData = self.HalfYearAnalyses.GetDataBase(f"patient_id = '{patient.get('id')}'")
            Tranclate = dict(zip([_[0] for _ in HALFYEAR_ANALYSES_FIELDS], [_[1] for _ in HALFYEAR_ANALYSES_FIELDS]))
            if BeforeTherapyData:
                BeforeTherapyData = BeforeTherapyData[0]
                info += "\nДанные до терапии:\n"
                for key, val in BeforeTherapyData.items():
                    if key != "patient_id" and key != 'id':
                        info += f"{' ' * 4}- {Tranclate[key]}: {val}\n"
            else:
                info += "\nДанные до терапии: нет данных.\n"

            # Вывод анализов
            analyses = self.Analyses.GetDataBase(f"patient_id = '{patient.get('id')}'")
            if analyses:
                grouped = {}
                for a in analyses:
                    date = a.get('date', '-')
                    grouped.setdefault(date, []).append(a)
                info += "\nАнализы:\n"
                for date in sorted(grouped.keys()):
                    group = grouped[date]
                    info += f"Дата: {date}\n"
                    for a in group:
                        info += f"  {a.get('analysis_type', '-')}: {a.get('result', '-')}\n"
            else:
                info += "\nАнализы: нет данных\n"

            # Half year analyses
            FullhalfYearAnalyses = self.HalfYearAnalyses.GetDataBase(f"patient_id = '{patient.get('id')}'")
            dataBeforeHalfYearAnalyses = FullhalfYearAnalyses[0] if FullhalfYearAnalyses else None
            halfYearAnalyses = None
            if FullhalfYearAnalyses and len(FullhalfYearAnalyses) > 1:
                halfYearAnalyses = FullhalfYearAnalyses[1:]
                grouped = {}
                for a in halfYearAnalyses:
                    date = a.get('Date', '-')
                    grouped.setdefault(date, []).append(a)
                info += "\nКонтроль каждые пол года:\n"
                for idx, date in enumerate(sorted(grouped.keys())):
                    group = grouped[date]
                    info += f"Контроль №{idx+1} | Дата: {date}\n"
                    for a in group:
                        for key, lable in self.HalfYearAnalyses.FIELDS:
                            if key != "Date":
                                info += f"  {lable}: {a.get(key, '-')}\n"

            else:
                info += "\nКонтроль: нет данных\n"
            self.SendMessage(message, info)
            # Кнопки: добавить анализ, изменить данные, изменить анализ
            NoofControls = len(halfYearAnalyses) if halfYearAnalyses else 0
            ButtonControl = f"Добавить {NoofControls+1}-й контроль"
            if not dataBeforeHalfYearAnalyses:
                ButtonControl = f"Добавить данные до терапии"

            if NoofControls == 0 and dataBeforeHalfYearAnalyses:
                keyboard = self.GetCustomKeyboard([["Изменить данные пациента"], ["Добавить анализ", "Изменить анализ"],
                                                   [ButtonControl, "Изменить данные до терапии"], ["Отмена"]])
            elif NoofControls >= 1:
                keyboard = self.GetCustomKeyboard([["Изменить данные пациента"], ["Добавить анализ", "Изменить анализ"],
                                                   [ButtonControl], ["Изменить данные до терапии", "Изменить данные контроля"], ["Отмена"]])
            else:
                keyboard = self.GetCustomKeyboard([["Изменить данные пациента"], ["Добавить анализ", "Изменить анализ"],
                                                   [ButtonControl], ["Отмена"]])
            self.SendMessage(message, "Выберите действие:", keyboard)
            self.NextStepHendler(message, self.PatientActionPrompt, patient, analyses, halfYearAnalyses, dataBeforeHalfYearAnalyses)
            break  # Только для первого найденного пациента, можно расширить

    @CommandDecorator
    def PatientActionPrompt(self, message, patient, analyses, halfYearAnalyses, dataBeforeHalfYearAnalyses):
        from re import fullmatch

        if message.text == "Добавить анализ":
            self.SendMessage(message, "Введите тип анализа:")
            self.NextStepHendler(message, self.AddAnalysisStep, patient, {})
        elif message.text == "Изменить данные пациента":
            # Список полей для изменения
            fields_keyboard = self.GetCustomKeyboard([[label] for key, label in self.Patients.FIELDS]+[["Отмена"]])
            self.SendMessage(message, "Выберите поле для изменения:", fields_keyboard)
            self.NextStepHendler(message, self.EditPatientFieldChoose, patient)
        elif message.text == "Изменить анализ":
            if not analyses:
                self.SendMessage(message, "У пациента нет анализов для изменения.")
                self._show_patients_search_result(message, [patient])
                return
            # Список анализов по дате и типу
            buttons = []
            for a in analyses:
                btn = f"{a.get('date', '-')} | {a.get('analysis_type', '-')}"
                buttons.append([btn])
            buttons.append(["Отмена"])
            self.SendMessage(message, "Выберите анализ для изменения:", self.GetCustomKeyboard(buttons))
            self.NextStepHendler(message, self.EditAnalysisChoose, analyses, patient)
        elif fullmatch(r"Добавить [0-9]+-й контроль", message.text) or message.text == "Добавить данные до терапии":
            from src.Client.halfyear_survey import start_halfyear_survey
            start_halfyear_survey(message, patient["id"])
            return
        elif message.text ==  "Изменить данные до терапии":
            if not dataBeforeHalfYearAnalyses:
                self.SendMessage(message, "Нет данных для изменения")
                self._show_patients_search_result(message, [patient])
                return
            from src.Client.halfyear_survey import halftear_edit_filed
            halftear_edit_filed(message, dataBeforeHalfYearAnalyses)
        elif message.text == "Изменить данные контроля":
            if len(halfYearAnalyses) <= 0:
                self.SendMessage(message, "Нет контрольных данных для изменения")
                message.text = f"{patient['id']}"
                self.FindPatientByField(message, "id")
                self._show_patients_search_result(message, [patient])
                return
            if len(halfYearAnalyses) == 1:
                from src.Client.halfyear_survey import halftear_edit_filed
                halftear_edit_filed(message, halfYearAnalyses[0])
            else:
                from src.Client.halfyear_survey import halftear_edit_choose
                txt = f"Выберете номер контроля для изменения: 1 - {len(halfYearAnalyses)}"
                NoofControls = len(halfYearAnalyses)
                btns = []
                for i in range(NoofControls):
                    if i % 5 == 0:
                        btns.append([])
                    btns[i // 5].append(str(i + 1))

                self.SendMessage(message, txt, self.GetCustomKeyboard(btns+[["Отмена"]]))
                self.NextStepHendler(message, halftear_edit_choose, halfYearAnalyses)

        elif message.text == "Отмена":
            self.SendMessage(message, "Операция завершена.")
        else:
            self.SendMessage(message, "Неизвестная команда.")
            self._show_patients_search_result(message, [patient])

    @CommandDecorator
    def EditPatientFieldChoose(self, message, patient):
        label = message.text.strip()
        if label == "Отмена":
            self.SendMessage(message, "Редактирование завершено.")
            self._show_patients_search_result(message, [patient])
            return
        key = None
        for k, l in self.Patients.FIELDS:
            if l == label:
                key = k
                break
        if not key:
            self.SendMessage(message, "Пожалуйста, выберите поле из списка.")
            self.NextStepHendler(message, self.EditPatientFieldChoose, patient)
            return

        # keyboard finder
        from src.Client.PatientReg import PATIENT_REG_FIELDS
        buttons = None
        for k, lable, btn in  PATIENT_REG_FIELDS:
            if k == key:
                buttons = self.GetCustomKeyboard(btn)
        self.SendMessage(message, f"Введите новое значение для поля '{label}':", keyboard=buttons)
        self.NextStepHendler(message, self.EditPatientFieldInput, patient, key, label)

    @CommandDecorator
    def EditPatientFieldInput(self, message, patient, key, label):
        new_value = message.text.strip()
        if self.Patients.Update({key: new_value}, f"id = '{patient.get('id')}'"):
            self.SendMessage(message, f"Поле '{label}' успешно обновлено!")
            AdminUser = self.Users.getUser(str(message.from_user.id))
            if AdminUser:
                log(f"{AdminUser} CHANGE PATIENT {patient} FIELD {label} TO {new_value}")
            else:
                log(f"NO NAME CHANGE PATIENT {patient} FIELD {label} TO {new_value}")
            # Снова предложить выбрать поле для изменения
            fields_keyboard = self.GetCustomKeyboard([[l] for k, l in self.Patients.FIELDS] + [["Отмена"]])
            self.SendMessage(message, "Выберите следующее поле для изменения или 'Отмена':", fields_keyboard)
            self.NextStepHendler(message, self.EditPatientFieldChoose, patient)
        else:
            self.SendMessage(message, f"Ошибка при обновлении поля '{label}'.")
            self._show_patients_search_result(message, [patient])

    @CommandDecorator
    def EditAnalysisChoose(self, message, analyses, patient):
        # Найти анализ по дате и типу
        choice = message.text.strip()

        if choice == "Отмена":
            self._show_patients_search_result(message, [patient])
            return
        for a in analyses:
            btn = f"{a.get('date', '-')} | {a.get('analysis_type', '-')}"
            if btn == choice:
                self.SendMessage(message, f"Введите новое значение результата анализа '{a.get('analysis_type', '-')}' за {a.get('date', '-')}: ")
                self.NextStepHendler(message, self.EditAnalysisInput, a, patient)
                return
        self.SendMessage(message, "Пожалуйста, выберите анализ из списка.")
        self.NextStepHendler(message, self.EditAnalysisChoose, analyses, patient)

    @CommandDecorator
    def EditAnalysisInput(self, message, analysis, patient):
        new_result = message.text.strip()
        if self.Analyses.Update({'result': new_result}, f"id = '{analysis.get('id')}'"):
            self.SendMessage(message, "Результат анализа успешно обновлён!")
            AdminUser = self.Users.getUser(str(message.from_user.id))
            if AdminUser:
                log(f"{AdminUser} CHANGE PATIENT {patient} ANALISIS {analysis} RESUALT TO {new_result}")
            else:
                log(f"NO NAME CHANGE PATIENT {patient} ANALISIS {analysis} RESUALT TO {new_result}")
        else:
            self.SendMessage(message, "Ошибка при обновлении анализа.")
        self._show_patients_search_result(message, [patient])

    @CommandDecorator
    def AddAnalysisStep(self, message, patient, analysis_data):
        if not analysis_data:
            analysis_data["patient_id"] = patient.get("id")
            analysis_data["analysis_type"] = message.text.strip()
            self.SendMessage(message, "Введите результат анализа:")
            self.NextStepHendler(message, self.AddAnalysisStep, patient, analysis_data)
        elif "result" not in analysis_data:
            analysis_data["result"] = message.text.strip()
            self.SendMessage(message, "Введите дату анализа (например, 25.07.2024):")
            self.NextStepHendler(message, self.AddAnalysisStep, patient, analysis_data)
        else:
            analysis_data["date"] = message.text.strip()
            if self.Analyses.Insert(analysis_data):
                self.SendMessage(message, "Анализ успешно добавлен!")
                user = self.Users.getUser(str(message.from_user.id))
                if user:
                    log(f"{user} ADD NEW ANALIZ: {analysis_data} IN PATIENT {patient}")
                else:
                    log(f"Uncommon user add ANALIZ {analysis_data} IN PATIENT {patient}!!!")
            else:
                self.SendMessage(message, "Ошибка при добавлении анализа.")
            self._show_patients_search_result(message, [patient])
