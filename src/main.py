from Users import USERS
from Patients import *
from os import environ

def load_environment() -> None:
    with open("bin/.env", "r") as f:
        key, val = f.readline().split('=')
        environ[key] = val

def main() -> None:
    load_environment()

if __name__ == "__main__":
    Users = USERS()
    Patients = PATIENTS()
    main()
    Users.ShowDataBase()
    Patients.ShowDataBase()