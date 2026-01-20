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
    game_id: int
    ranking: int
    gemiddelde_waarde: float
    beste_waarde: float
    exactheid: float
    aantal_correct: int
    aantal_fout: int
    aantal_telaat: int
    correcte_rondewaarden: list[CorrecteRondeWaarde]

class GameVoorOverzicht(BaseModel):
    game_naam: str
    tag: str
    highscore: float
    eenheid: str

class Moeilijkheid(BaseModel):
    moeilijkheid_id: int
    moeilijkheid: str
    snelheid: int   

class Ronde(BaseModel):
    ronde_id: int
    nummer: int

class LeaderboardItem(BaseModel):
    plaats: int
    gebruikersnaam: str
    waarde: float

class DetailGame(BaseModel):
    list_moeilijkheden: list[Moeilijkheid]
    aantal_rondes: list[Ronde]
    game_naam: str
    game_beschrijving: str
    leaderboard: list[LeaderboardItem]

class GameVoorFilter(BaseModel):
    game_id: int
    game_naam: str

class FiltersVoorHistorie(BaseModel):
    game_id: int
    datum: str | None = None
    gebruikersnaam: str | None = None

class TrainingVoorHistorie(BaseModel):
    training_id: int
    gebruikersnaam: str
    start_tijd: str
    waarde: float
    eenheid:str

class RondeWaardenVoorDetails(BaseModel):
    game_id: int
    gemmidelde_waarde: float
    beste_waarde: float
    ranking: int
    exactheid: float
    lijst_voor_grafiek: list[CorrecteRondeWaarde]
    aantal_correct: int
    aantal_fout: int
    aantal_telaat: int

class MoeilijkheidVoorLeaderboard(BaseModel):
    moeilijkheid_id: int
    moeilijkheid: str




    

