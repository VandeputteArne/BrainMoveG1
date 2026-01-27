from fastapi import APIRouter
from typing import Optional
from backend.src.repositories.data_repository import DataRepository
from backend.src.models.models import LeaderboardItem, MoeilijkheidVoorLeaderboard

router = APIRouter(
    prefix="/leaderboard",
    tags=["Leaderboard"]
)


@router.get("/games/{game_id}/{max}", response_model=list[LeaderboardItem], summary="Haal de leaderboard op voor een specifiek spel")
async def get_leaderboard(game_id: int, max: int):
    leaderboard = DataRepository.get_leaderboard_for_game(game_id, max)
    if(game_id == 5):
        #als de gameid 5 is mag je deze uit de lijst halen
        leaderboard = [item for item in leaderboard if item.gebruikersnaam != "ColorBattleAI"]
    return leaderboard


@router.get("/filters/{game_id}", response_model=list[MoeilijkheidVoorLeaderboard], summary="Haal de lijst van spellen op voor filterdoeleinden in de leaderboard")
async def get_moeilijkheden_for_filter(game_id: int):
    moeilijkheden = DataRepository.get_moeilijkheden_for_game(game_id)
    if(game_id == 5):
        #als de gameid 5 is mag je deze uit de lijst halen
        moeilijkheden = [item for item in moeilijkheden if item.moeilijkheid != "AI"]
    return moeilijkheden


@router.get("/overview/{game_id}/{moeilijkheids_id}", response_model=list[LeaderboardItem], summary="Haal een overzicht op van alle spellen met hun highscores voor de leaderboard")
async def get_leaderboard_overview(game_id: int, moeilijkheids_id: int, datum: Optional[str] = None):
    trainingen = DataRepository.get_leaderboard_with_filters(game_id, moeilijkheids_id, datum)
    if(game_id == 5):
        #als de gameid 5 is mag je deze uit de lijst halen
        trainingen = [item for item in trainingen if item.gebruikersnaam != "ColorBattleAI"]
    return trainingen
