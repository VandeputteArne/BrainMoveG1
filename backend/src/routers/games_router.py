from fastapi import APIRouter
from backend.src.repositories.data_repository import DataRepository
from backend.src.models.models import GameVoorOverzicht, DetailGame, GameVoorFilter

router = APIRouter(
    prefix="/games",
    tags=["Games"],
)

@router.get("/overview", response_model=list[GameVoorOverzicht], summary="Haal een overzicht op van alle spellen met hun highscores", tags=["Games"])
async def get_games_overview():
    games = DataRepository.get_all_games()
    
    result = []
    for game in games:
        game_id = game['GameId']
        
        # GameId 1 = Color Sprint: laagste gemiddelde tijd van rondewaarden
        # GameId 2+ = Memory etc: hoogste aantal kleuren gebruikt
        if game_id == 1 or game_id == 3 or game_id == 4 or game_id == 5:
            highscore = DataRepository.get_best_avg_for_game(game_id, use_min=True)
        else:
            highscore = DataRepository.get_max_kleuren_for_game(game_id)
        
        result.append(GameVoorOverzicht(
            game_naam=game['GameNaam'],
            tag=game['Tag'].capitalize(),
            highscore=round(highscore, 2),
            eenheid=game['Eenheid']
        ))
    
    return result

@router.get("/details/{game_id}", response_model=DetailGame, summary="Haal de details op voor een specifiek spel", tags=["Games"])
async def get_game_details(game_id: int):
    details = DataRepository.get_game_details(game_id)
    return details

@router.get("/filters", response_model=list[GameVoorFilter], summary="Haal de lijst van spellen op voor filterdoeleinden", tags=["Games"])
async def get_games_for_filter():
    games = DataRepository.get_games_for_filter()
    return games