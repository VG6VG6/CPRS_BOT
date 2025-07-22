import DB
from DB import log

class PATIENTS(DB.DATA_BASE):

    def __init__(self):
        Patients_DB_Fields = {
        "id": "INTEGER PRIMARY KEY",
        "Name": "TEXT NOT NULL",
        "Surname": "TEXT NOT NULL",
        "Patronymic": "TEXT NOT NULL",
        "Passport": "TEXT NOT NULL",
        "Phone": "TEXT NOT NULL",
        "Snils": "TEXT NOT NULL",
        "Name_of_the_medical_institution_from_where_it_was_sent": "TEXT NOT NULL",
        "Surgical_treatment_for_CRF": "TEXT NOT NULL",
        "Noof_operation": "INT NOT NULL",
        "Presence_of_aspirin_triad": "TEXT NOT NULL",
        "Presence_of_bronchial_asthma": "TEXT NOT NULL",
        "Presence_of_other_T2_inflammations[AD,EE,UZP]": "TEXT NOT NULL",
        "Commission_date": "TEXT NOT NULL",
        "Results_of_the_commission": "TEXT NOT NULL",
        "Initiation_date": "TEXT NOT NULL",
        "Biological_status": "TEXT NOT NULL",
        "Therapy_status": "TEXT NOT NULL"
        }
        super().__init__("PATIENTS", Patients_DB_Fields)
        # Default dictionary with all fields of Patient data. It will be filled in DB class __init__ method
        self.DefaultFields = super().GetDefaultFields()