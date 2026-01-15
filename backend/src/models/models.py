from pydantic import BaseModel

class Instellingen(BaseModel):
    game_id: int
    gebruikersnaam: str
    moeilijkheids_id: int
    snelheid: int
    ronde_id : int
    rondes: int
    kleuren: list[str]

class RondeWaarde(BaseModel):
    trainings_id: int
    ronde_nummer: int
    waarde: int
    uitkomst: str

class Resultaat(BaseModel):
    ranking: int
    gemiddelde_waarde: float
    beste_waarde: float
    exactheid: float
    aantal_correct: int
    aantal_fout: int
    aantal_telaat: int