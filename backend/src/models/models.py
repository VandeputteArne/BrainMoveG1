from pydantic import BaseModel

class Instellingen(BaseModel):
    game_id: int
    gebruikersnaam: str
    moeilijkheids_id: int
    snelheid: int
    ronde_id : int
    rondes: int
    kleuren: list[str]

class Training(BaseModel):
    start_tijd: str
    aantal_kleuren: int
    gebruikers_id: int
    ronde_id: int
    moeilijkheids_id: int
    game_id: int

class RondeWaarde(BaseModel):
    trainings_id: int
    ronde_nummer: int
    waarde: float
    uitkomst: str

class CorrecteRondeWaarde(BaseModel):
    ronde_nummer: int
    waarde: float

class Resultaat(BaseModel):
    ranking: int
    gemiddelde_waarde: float
    beste_waarde: float
    exactheid: float
    aantal_correct: int
    aantal_fout: int
    aantal_telaat: int
    correcte_rondewaarden: list[CorrecteRondeWaarde]