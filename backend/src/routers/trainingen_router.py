from typing import Union
from fastapi import APIRouter
from backend.src.repositories.data_repository import DataRepository
from backend.src.models.models import StatistiekenVoorColorSprint, StatistiekenVoorMemoryGame, CorrecteRondeWaarde, TrainingVoorHistorie

router = APIRouter(
    prefix="/trainingen",
    tags=["Trainingen"]
)


@router.get("/laatste_rondewaarden",)
async def get_laatste_rondewaarden():
    list_rondewaarden = DataRepository.get_last_rondewaarden_from_last_training()

    gemiddelde_tijd = list_rondewaarden and sum(float(item.waarde) for item in list_rondewaarden) / len(list_rondewaarden) or 0
    beste_tijd = list_rondewaarden and min(float(item.waarde) for item in list_rondewaarden) or 0

    # Bepaal ID van de laatst toegevoegde training en vraag ranking op
    last_training_id = DataRepository.get_last_training_id()

     
    gebruikersnaam = DataRepository.get_gebruikersnaam_by_trainingid(last_training_id)
    exactheid = len([item for item in list_rondewaarden if item.uitkomst.lower() == 'correct']) / len(list_rondewaarden) * 100 if list_rondewaarden else 0

    aantal_correct = len([item for item in list_rondewaarden if item.uitkomst.lower() == 'correct'])
    aantal_fout = len([item for item in list_rondewaarden if item.uitkomst.lower() == 'fout'])
    aantal_telaat = len([item for item in list_rondewaarden if item.uitkomst.lower() == 'te laat'])
    
    print(f"DEBUG: aantal_correct = {aantal_correct}, aantal_fout = {aantal_fout}, aantal_telaat = {aantal_telaat}")

    #ophalen welke rondes met hun rondenummers en waardes waar correct voor de grafiek
    correcte_rondewaarden = [item for item in list_rondewaarden if item.uitkomst.lower() == 'correct']
    # Hier kun je verdere verwerking van correcte_rondewaarden toevoegen, bijvoorbeeld voor een grafiek
    correcte_rondewaarden_data = [CorrecteRondeWaarde(ronde_nummer=item.ronde_nummer, waarde=item.waarde) for item in correcte_rondewaarden]

    game_id = DataRepository.get_gameid_by_trainingid(last_training_id) if last_training_id else None
    if(game_id ==1 or game_id == 3):
        ranking = DataRepository.get_ranking_for_onetraining(last_training_id)
        return StatistiekenVoorColorSprint(
        game_id=game_id or 0,
        gebruikersnaam=gebruikersnaam or "",
        ranking=ranking or 0,
        gemiddelde_waarde=round(gemiddelde_tijd, 2),
        beste_waarde=round(beste_tijd, 2),
        exactheid=round(exactheid, 0),
        aantal_correct=aantal_correct,
        aantal_fout=aantal_fout,
        aantal_telaat=aantal_telaat,
        lijst_voor_grafiek=correcte_rondewaarden_data
    )
    if(game_id ==2):
        totaal_aantal_rondes = DataRepository.get_totale_aantal_rondes_by_trainingid(last_training_id) if last_training_id else 0   
        exactheid_memory = aantal_correct / totaal_aantal_rondes * 100 if totaal_aantal_rondes > 0 else 0
        correcte_rondewaarden_memory = [item for item in list_rondewaarden if item.uitkomst.lower() == 'correct']

        #nu wil ik van de correcte rondes de avg tijd berekene per ronde, dit aan de hand van de ronde nummers, dus deel de reactietijden door het ronde nummer
        correcte_rondewaarden_data_memory = [
            CorrecteRondeWaarde(
                ronde_nummer=item.ronde_nummer,
                waarde=round(float(item.waarde) / item.ronde_nummer, 2)
            ) for item in correcte_rondewaarden_memory
        ]

        aantal_correct_memory = len([item for item in list_rondewaarden if item.uitkomst.lower() == 'correct'])
        aantal_fout_memory = len([item for item in list_rondewaarden if item.uitkomst.lower() == 'fout'])
        aantal_rondes_niet_gespeeld = totaal_aantal_rondes - len(list_rondewaarden)

        #gemiddelde waarde is gwn het gemiddelde van de waardes van de correcte rondes (gedeeld door ronde_nummer)
        gemiddelde_waarde_memory = sum(item.waarde for item in correcte_rondewaarden_data_memory) / len(correcte_rondewaarden_data_memory) if correcte_rondewaarden_data_memory else 0

        ranking = DataRepository.get_ranking_for_onetraining(last_training_id) or 0


        return StatistiekenVoorMemoryGame(
        game_id=game_id or 0,
        gebruikersnaam=gebruikersnaam or "",
        ranking=ranking or 0,
        aantal_kleuren=aantal_correct,
        gemiddelde_waarde=round(gemiddelde_waarde_memory, 2),
        exactheid=round(exactheid_memory, 0),
        lijst_voor_grafiek=correcte_rondewaarden_data_memory,
        aantal_correct=aantal_correct_memory,
        aantal_fout=aantal_fout_memory,
        aantal_rondes_niet_gespeeld=aantal_rondes_niet_gespeeld
    )

@router.get("/historie/{game_id}", response_model=list[TrainingVoorHistorie], summary="Haal de trainingshistorie op voor een gebruiker")
async def get_training_history(game_id: int, gebruikersnaam: str | None = None, datum: str | None = None):
    # Converteer datum van dd-mm-yyyy naar yyyy-mm-dd
    if datum:
        try:
            datum_parts = datum.split('-')
            if len(datum_parts) == 3:
                datum = f"{datum_parts[2]}-{datum_parts[1]}-{datum_parts[0]}"
        except Exception:
            pass  # Gebruik originele datum als conversie mislukt
    
    trainingen = DataRepository.get_trainingen_with_filters(game_id, datum, gebruikersnaam)
    return trainingen

@router.get("/{training_id}/details", response_model=Union[StatistiekenVoorColorSprint, StatistiekenVoorMemoryGame], summary="Haal de details op voor een specifieke training")
async def get_training_details(training_id: int):
    rondewaarden = DataRepository.get_allerondewaarden_by_trainingsId(training_id)
    game_id = DataRepository.get_gameid_by_trainingid(training_id)
    gebruikersnaam = DataRepository.get_gebruikersnaam_by_trainingid(training_id)

    if(game_id==1 or game_id==3):
        return StatistiekenVoorColorSprint(
        game_id=game_id or 0,
        gebruikersnaam=gebruikersnaam or "",
        gemiddelde_waarde=round(sum(float(item.waarde) for item in rondewaarden) / len(rondewaarden), 2) if rondewaarden else 0,
        beste_waarde=round(min(float(item.waarde) for item in rondewaarden), 2) if rondewaarden else 0,
        ranking=DataRepository.get_ranking_for_onetraining(training_id) or 0,
        exactheid=round(len([item for item in rondewaarden if item.uitkomst == 'correct']) / len(rondewaarden) * 100, 0) if rondewaarden else 0,
        lijst_voor_grafiek=[CorrecteRondeWaarde(ronde_nummer=item.ronde_nummer, waarde=item.waarde) for item in rondewaarden if item.uitkomst == 'correct'],
        aantal_correct=len([item for item in rondewaarden if item.uitkomst == 'correct']),
        aantal_fout=len([item for item in rondewaarden if item.uitkomst == 'fout']),
        aantal_telaat=len([item for item in rondewaarden if item.uitkomst == 'te laat'])
        )
    if(game_id==2):
        return StatistiekenVoorMemoryGame(
        game_id=game_id or 0,
        gebruikersnaam=gebruikersnaam or "",
        ranking=DataRepository.get_ranking_for_onetraining(training_id) or 0,
        aantal_kleuren=len(rondewaarden),
        gemiddelde_waarde=round(sum(float(item.waarde) for item in rondewaarden) / len(rondewaarden), 2) if rondewaarden else 0,
        #bereken de exactheid voor memory game aan de hand van de voltooide rondes t.o.v. het totale aantal rondes
        exactheid=round(len([item for item in rondewaarden if item.uitkomst == 'correct']) / DataRepository.get_totale_aantal_rondes_by_trainingid(training_id) * 100, 0) if rondewaarden else 0,
        correcte_rondewaarden=[CorrecteRondeWaarde(ronde_nummer=item.ronde_nummer, waarde=round(float(item.waarde) / item.ronde_nummer, 2)) for item in rondewaarden if item.uitkomst == 'correct'],
        aantal_correct=len([item for item in rondewaarden if item.uitkomst == 'correct']),
        aantal_fout=len([item for item in rondewaarden if item.uitkomst == 'fout']),
        aantal_rondes_niet_gespeeld=DataRepository.get_totale_aantal_rondes_by_trainingid(training_id) - len(rondewaarden)
        )