import src.Server.DB as DB
from src.Server.DB import log

class ANALYSES(DB.DATA_BASE):
    def __init__(self):
        Analyses_DB_Fields = {
            "id": "INTEGER PRIMARY KEY",
            "patient_id": "INTEGER NOT NULL",
            "analysis_type": "TEXT NOT NULL",
            "result": "TEXT NOT NULL",
            "date": "TEXT NOT NULL"
        }
        self.FIELDS = [
            ("patient_id", "Номер пациента"),
            ("analysis_type", "Тип анализа"),
            ("result", "Результат"),
            ("date", "Дата")
        ]
        super().__init__("ANALYSES", Analyses_DB_Fields)
        self.DefaultFields = super().GetDefaultFields() 