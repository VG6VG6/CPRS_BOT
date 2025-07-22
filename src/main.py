from Users import USERS
from Patients import *
from os import environ
from tools import log
import sys

def load_environment() -> None:
    with open("bin/.env", "r") as f:
        try:
            for line in f:
                key, val = line.split('=')
                environ[key] = val
        except:
            print("Fatal error. Error loading data from .env file.")


def main() -> None:
    sys.stdout = open("bin/LOG.txt", 'a')
    log("a")
    Users = USERS()
    Patients = PATIENTS()
    load_environment()
    Users.ShowDataBase()
    Patients.ShowDataBase()

if __name__ == "__main__":
    main()