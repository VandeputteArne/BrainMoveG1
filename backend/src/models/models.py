from pydantic import BaseModel

class Instellingen(BaseModel):
    game_id: int
    gebruikersnaam: str
    moeilijkheids_id: int
    snelheid: int
    ronde_id : int
    rondes: int
    kleuren: list[str]

class ColorBattleInstellingen(BaseModel):
    game_id: int
    speler1_naam: str
    speler2_naam: str
    moeilijkheids_id: int
    snelheid: int
    ronde_id: int
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
    gebruikersnaam: str
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
    eenheid: str

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

class MoeilijkheidVoorLeaderboard(BaseModel):
    moeilijkheid_id: int
    moeilijkheid: str

class StatistiekenVoorMemoryGame(BaseModel):
    game_id: int
    gebruikersnaam: str
    ranking: int
    aantal_kleuren: int
    gemiddelde_waarde: float
    exactheid: float
    lijst_voor_grafiek: list[CorrecteRondeWaarde]
    aantal_correct: int
    aantal_fout: int
    aantal_rondes_niet_gespeeld: int

class StatistiekenVoorColorSprint(BaseModel):
    game_id: int
    gebruikersnaam: str
    gemiddelde_waarde: float
    beste_waarde: float
    ranking: int
    exactheid: float
    lijst_voor_grafiek: list[CorrecteRondeWaarde]
    aantal_correct: int
    aantal_fout: int
    aantal_telaat: int

class UitschakelenRequest(BaseModel):
    inputGebruiker: str

class ColorBattleRondeResultaat(BaseModel):
    rondenummer: int
    speler1_kleur: str
    speler2_kleur: str
    speler1_tijd: float
    speler2_tijd: float
    speler1_uitkomst: str
    speler2_uitkomst: str
    ronde_winnaar: int | None  # 1, 2, or None for tie

class ColorBattleEindResultaat(BaseModel):
    speler1_naam: str
    speler2_naam: str
    speler1_correct: int
    speler2_correct: int
    speler1_totaal_tijd: float
    speler2_totaal_tijd: float
    winnaar: int | None  # 1, 2, or None for tie
    rondes: list[ColorBattleRondeResultaat]
    





    

