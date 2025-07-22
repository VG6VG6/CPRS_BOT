import datetime

# Logging function
def log(*args, **kwargs):
    Now = datetime.datetime.now()
    current = Now.strftime("%d.%m.%Y|%H:%M:%S")
    print(f"[{current}]", end=" ")
    print(*args, **kwargs)
