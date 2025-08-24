import datetime
import re

class Singleton(object):
    _instance = None

    def __new__(class_, *args, **kwargs):
        if not isinstance(class_._instance, class_):
            class_._instance = object.__new__(class_)
        return class_._instance

LogFile = None

def log(*args, **kwargs):
    global LogFile
    if LogFile is None:
        LogFile = open("bin/LOG.txt", 'a', encoding='utf-8')  # открываем один раз в режиме append

    now = datetime.datetime.now().strftime("%d.%m.%Y|%H:%M:%S")
    LogFile.write(f"[{now}] ")
    LogFile.write(' '.join(map(str, args)) + "\n")
    LogFile.flush()  # чтобы запись была сразу

def validate_fio(fio: str) -> bool:
    # ФИО: три слова, только буквы, первая буква заглавная
    parts = fio.strip().split()
    if len(parts) != 3:
        return False
    return all(re.match(r'^[А-ЯЁA-Z][а-яёa-z]*$', part) for part in parts)

def validate_phone(phone: str) -> str | None:
    phone = re.sub(r'\D', '', phone)  # убираем все нецифры
    if len(phone) == 11 and (phone.startswith('7') or phone.startswith('8')):
        return f'+7{phone[1:]}'  # нормализуем
    return None  # если не подходит

def validate_passport(passport: str) -> str | None:
    digits = re.sub(r'\D', '', passport)  # оставляем только цифры
    if len(digits) == 10:
        return f'{digits[:4]} {digits[4:]}'
    return None

def validate_snils(snils: str) -> str | None:
    digits = re.sub(r'\D', '', snils)
    if len(digits) == 11:
        return f'{digits[:3]}-{digits[3:6]}-{digits[6:9]} {digits[9:]}'
    return None

def validate_date(date_str: str) -> str | None:
    if date_str == "-":
        return "-"
    try:
        date_obj = datetime.datetime.strptime(date_str, "%d.%m.%Y")
        return date_obj.strftime("%d.%m.%Y")
    except ValueError:
        return None