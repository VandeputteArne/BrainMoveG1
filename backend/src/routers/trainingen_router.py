from typing import Union
from fastapi import APIRouter
from backend.src.repositories.data_repository import DataRepository
from backend.src.models.models import StatistiekenVoorColorSprint, StatistiekenVoorMemoryGame, StatistiekenVoorColorBattle, CorrecteRondeWaarde, TrainingVoorHistorie, ColorBattleCorrecteRonde
import logging

router = APIRouter(
    prefix="/trainingen",
    tags=["Trainingen"]
)


@router.get("/laatste_rondewaarden", response_model=Union[StatistiekenVoorColorSprint, StatistiekenVoorMemoryGame, StatistiekenVoorColorBattle])
async def get_laatste_rondewaarden():
    list_rondewaarden = DataRepository.get_last_rondewaarden_from_last_training()

    gemiddelde_tijd = list_rondewaarden and sum(float(item.waarde) for item in list_rondewaarden) / len(list_rondewaarden) or 0
    beste_tijd = list_rondewaarden and min(float(item.waarde) for item in list_rondewaarden) or 0

    # Bepaal ID van de laatst toegevoegde training en vraag ranking op
    last_training_id = DataRepository.get_last_training_id()

    logging.debug(f"Last training ID: {last_training_id}")
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
    if(game_id ==1 or game_id == 3 or game_id ==4):
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
    
    if game_id == 5:  # Color Battle
        # Voor Color Battle hebben we 2x zoveel rondewaarden (beide spelers)
        totaal_rondes = len(list_rondewaarden) // 2 if list_rondewaarden else 0
        
        # Haal beide spelernamen op
        speler1_naam, speler2_naam = DataRepository.get_colorbattle_spelernamen_by_trainingid(last_training_id)
        if not speler1_naam:
            speler1_naam = gebruikersnaam or "Speler 1"
        if not speler2_naam:
            speler2_naam = "Speler 2"
        
        # Split rondewaarden per speler (even indices = speler1, oneven = speler2)
        speler1_waarden = [list_rondewaarden[i] for i in range(0, len(list_rondewaarden), 2)] if list_rondewaarden else []
        speler2_waarden = [list_rondewaarden[i] for i in range(1, len(list_rondewaarden), 2)] if list_rondewaarden else []
        
        # Bereken statistieken per speler
        speler1_correct = len([r for r in speler1_waarden if r.uitkomst.lower() == 'correct'])
        speler1_fout = len([r for r in speler1_waarden if r.uitkomst.lower() == 'te laat'])
        speler1_totaal_tijd = sum(float(r.waarde) for r in speler1_waarden)
        
        speler2_correct = len([r for r in speler2_waarden if r.uitkomst.lower() == 'correct'])
        speler2_fout = len([r for r in speler2_waarden if r.uitkomst.lower() == 'te laat'])
        speler2_totaal_tijd = sum(float(r.waarde) for r in speler2_waarden)
        
        # Bepaal winnaar
        winnaar = None
        if speler1_correct > speler2_correct:
            winnaar = speler1_naam
        elif speler2_correct > speler1_correct:
            winnaar = speler2_naam
        elif speler1_totaal_tijd < speler2_totaal_tijd:
            winnaar = speler1_naam
        elif speler2_totaal_tijd < speler1_totaal_tijd:
            winnaar = speler2_naam
        
        # Bouw lijst met correcte rondes voor grafiek
        lijst_voor_grafiek = []
        for i in range(totaal_rondes):
            if i < len(speler1_waarden) and i < len(speler2_waarden):
                # Voeg alleen rondes toe waar iemand het juist had
                if speler1_waarden[i].uitkomst == 'correct':
                    lijst_voor_grafiek.append(ColorBattleCorrecteRonde(
                        ronde_nummer=speler1_waarden[i].ronde_nummer,
                        waarde=float(speler1_waarden[i].waarde),
                        speler_naam=speler1_naam
                    ))
                elif speler2_waarden[i].uitkomst == 'correct':
                    lijst_voor_grafiek.append(ColorBattleCorrecteRonde(
                        ronde_nummer=speler2_waarden[i].ronde_nummer,
                        waarde=float(speler2_waarden[i].waarde),
                        speler_naam=speler2_naam
                    ))
        
        return StatistiekenVoorColorBattle(
            game_id=game_id,
            speler1_naam=speler1_naam,
            speler2_naam=speler2_naam,
            speler1_correct=speler1_correct,
            speler2_correct=speler2_correct,
            speler1_fout=speler1_fout,
            speler2_fout=speler2_fout,
            winnaar=winnaar,
            lijst_voor_grafiek=lijst_voor_grafiek
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

@router.get("/{training_id}/details", response_model=Union[StatistiekenVoorColorSprint, StatistiekenVoorMemoryGame, StatistiekenVoorColorBattle], summary="Haal de details op voor een specifieke training")
async def get_training_details(training_id: int):
    rondewaarden = DataRepository.get_allerondewaarden_by_trainingsId(training_id)
    game_id = DataRepository.get_gameid_by_trainingid(training_id)
    gebruikersnaam = DataRepository.get_gebruikersnaam_by_trainingid(training_id)

    if(game_id==1 or game_id==3 or game_id == 4):
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
        lijst_voor_grafiek=[CorrecteRondeWaarde(ronde_nummer=item.ronde_nummer, waarde=round(float(item.waarde) / item.ronde_nummer, 2)) for item in rondewaarden if item.uitkomst == 'correct'],
        aantal_correct=len([item for item in rondewaarden if item.uitkomst == 'correct']),
        aantal_fout=len([item for item in rondewaarden if item.uitkomst == 'fout']),
        aantal_rondes_niet_gespeeld=DataRepository.get_totale_aantal_rondes_by_trainingid(training_id) - len(rondewaarden)
        )
    
    if(game_id == 5):
        return StatistiekenVoorColorBattle(
            game_id=game_id,
            speler1_naam=DataRepository.get_colorbattle_spelernamen_by_trainingid(training_id)[0],
            speler2_naam=DataRepository.get_colorbattle_spelernamen_by_trainingid(training_id)[1],
            speler1_correct=len([item for item in rondewaarden[::2] if item.uitkomst == 'correct']),
            speler2_correct=len([item for item in rondewaarden[1::2] if item.uitkomst == 'correct']),
            speler1_fout=len([item for item in rondewaarden[::2] if item.uitkomst == 'te laat']),
            speler2_fout=len([item for item in rondewaarden[1::2] if item.uitkomst == 'te laat']),
            winnaar=DataRepository.get_colorbattle_winnaar_by_trainingid(training_id),
            lijst_voor_grafiek=[
                ColorBattleCorrecteRonde(
                    ronde_nummer=item.ronde_nummer,
                    waarde=float(item.waarde),
                    speler_naam=DataRepository.get_colorbattle_spelernamen_by_trainingid(training_id)[0] if index % 2 == 0 else DataRepository.get_colorbattle_spelernamen_by_trainingid(training_id)[1]
                )
                for index, item in enumerate(rondewaarden) if item.uitkomst == 'correct'
            ]
        )
    