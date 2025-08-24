import src.Server.DB as DB
from src.Server.DB import log

class PATIENTS(DB.DATA_BASE):

    def __init__(self):
        from src.Client.PatientReg import PATIENT_REG_FIELDS

        Patients_DB_Fields = {"id": "INTEGER PRIMARY KEY"}
        for name, ruName, btn in PATIENT_REG_FIELDS:
            Patients_DB_Fields[name] = "TEXT NOT NULL"
        self.FIELDS = list((key, lable) for key, lable, btn in PATIENT_REG_FIELDS)

        super().__init__("PATIENTS", Patients_DB_Fields)
        # Default dictionary with all fields of Patient data. It will be filled in DB class __init__ method
        self.DefaultFields = super().GetDefaultFields()