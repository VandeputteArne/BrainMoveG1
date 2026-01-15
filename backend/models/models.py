from pydantic import BaseModel

class Instellingen(BaseModel):
    game_id: int
    gebruikersnaam: str
    moeilijkheids_id: int
    snelheid: int
    ronde_id : int
    rondes: int
    kleuren: list[str]