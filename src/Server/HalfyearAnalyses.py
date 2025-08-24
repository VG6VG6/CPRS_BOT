import src.Server.DB as DB

class HALF_YEAR_ANALYSES(DB.DATA_BASE):

    def __init__(self):
        from src.Client.halfyear_survey import HALFYEAR_ANALYSES_FIELDS

        Patients_DB_Fields = {"id": "INTEGER PRIMARY KEY", "patient_id": "INTEGER NOT NULL"}
        for name, ruName, btn in HALFYEAR_ANALYSES_FIELDS:
            Patients_DB_Fields[name] = "TEXT NOT NULL"
        self.FIELDS = list((key, lable) for key, lable, btn in HALFYEAR_ANALYSES_FIELDS)

        super().__init__("HALF_YEAR_ANALYSES", Patients_DB_Fields)

        self.DefaultFields = super().GetDefaultFields()