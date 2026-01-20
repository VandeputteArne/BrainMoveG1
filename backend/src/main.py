import logging
import asyncio
import datetime
import threading
import fastapi
import socketio
import uvicorn
import random
import time
import sys
import os
from typing import Union
from contextlib import asynccontextmanager # <--- 1. Toegevoegd

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, project_root)


from backend.src.services.device_manager import DeviceManager
from backend.src.repositories.data_repository import DataRepository
from backend.src.models.models import (
    FiltersVoorHistorie,
    GameVoorFilter,
    Instellingen,
    LeaderboardItem,
    Moeilijkheid,
    MoeilijkheidVoorLeaderboard,
    RondeWaarde,
    Resultaat,
    Training,
    CorrecteRondeWaarde,
    GameVoorOverzicht,
    DetailGame,
    TrainingVoorHistorie,
    RondeWaardenVoorDetails,
    StatistiekenVoorMemoryGame,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

@asynccontextmanager
async def lifespan(app: FastAPI):
    scan_task = asyncio.create_task(device_manager.start_apparaat_scan())
    device_manager._scan_taak = scan_task
    
    yield # App draait hier
    
    await device_manager.stop_apparaat_scan()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HARDWARE_DELAY = float(os.getenv("HARDWARE_DELAY", "0.07"))

sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    ping_interval=5,
    ping_timeout=3,
    always_connect=True,
)
sio_app = socketio.ASGIApp(sio, app)
device_manager = DeviceManager(sio=sio)

global game_id
global gebruikersnaam
global moeilijkheids_id
global snelheid
global ronde_id
global rondes
global kleuren
global starttijd

async def colorgame(aantal_rondes, kleuren, snelheid):
    # Maak mapping ESP-ID -> kleur gebaseerd op de volgorde van verbonden apparaten
    verbonden_apparaten = sorted(device_manager.apparaten.keys())
    
    apparaat_id_mapping = {}
    for idx, apparaat_naam in enumerate(verbonden_apparaten):
        if idx < len(kleuren):
            apparaat_id_mapping[idx] = kleuren[idx]
    
    # Mapping op basis van ESP naam (indien kleur in naam zit)
    kleur_mapping = {}
    for apparaat_naam in verbonden_apparaten:
        for kleur in kleuren:
            if kleur.lower() in apparaat_naam.lower():
                kleur_mapping[apparaat_naam] = kleur
                break
    
    colorgame_rondes = []
    aantal_correct = 0
    aantal_fout = 0
    aantal_telaat = 0

    rondetijden = {}
    max_tijd = float(snelheid)
    
    # Callback ipv laatste detectie dict
    detectie_event = asyncio.Event()
    detected_device = {}
    baseline_apparaten = set()

    def on_detectie(gebeurtenis):
        if gebeurtenis["apparaat_naam"] not in baseline_apparaten:
            detected_device.clear()
            detected_device.update(gebeurtenis)
            detectie_event.set()

    device_manager.zet_detectie_callback(on_detectie)

    await device_manager.start_alle()
    await asyncio.sleep(0.05)

    for ronde_idx in range(aantal_rondes):
        device_manager.verwijder_alle_laatste_detecties()
        ronde = ronde_idx + 1

        gekozen_kleur = random.choice(kleuren).upper()
        await sio.emit('gekozen_kleur', {'rondenummer': ronde, 'maxronden': aantal_rondes, 'kleur': gekozen_kleur})
        await asyncio.sleep(0)  # Flush socket
        print("Frontend socketio:", gekozen_kleur.upper())

        await device_manager.set_correct_kegel(gekozen_kleur)

        baseline_detecties = device_manager.verkrijg_alle_laatste_detecties()
        baseline_apparaten = set(baseline_detecties.keys())
        if baseline_apparaten:
            print(f"Voorgaande detecties genegeerd: {', '.join(baseline_apparaten)}")

        detectie_event.clear()
        detected_device.clear()
        device_manager.verwijder_alle_laatste_detecties()

        starttijd = time.time()

        await detectie_event.wait()
        eindtijd = time.time()
        reactietijd = round(eindtijd - starttijd, 2) - HARDWARE_DELAY

        print(detected_device)

        # Bepaal welke kleur gedetecteerd is
        gedetecteerde_esp_naam = detected_device["apparaat_naam"]
        device_id = detected_device.get("apparaat_id", None)
        
        # Probeer kleur te bepalen
        apparaatkleur = None
        
        if gedetecteerde_esp_naam in kleur_mapping:
            apparaatkleur = kleur_mapping[gedetecteerde_esp_naam]
        elif device_id is not None:
            if isinstance(device_id, str) and device_id.isdigit():
                device_id = int(device_id)
            if isinstance(device_id, int) and device_id in apparaat_id_mapping:
                apparaatkleur = apparaat_id_mapping[device_id]

        if apparaatkleur is None:
            print(f"Fout: Geen kleur gevonden voor {gedetecteerde_esp_naam} (device_id {device_id})")
            aantal_fout += 1
            colorgame_rondes.append({
                "rondenummer": ronde,
                "waarde": reactietijd,
                "uitkomst": "fout",
            })
            continue

        # Vergelijk kleuren
        if(reactietijd > max_tijd):
            print("Te laat gereageerd!")
            reactietijd = max_tijd
            status = "te laat"
            aantal_telaat += 1
        elif apparaatkleur.strip().lower() == gekozen_kleur.strip().lower():
            print("Correcte kleur gedetecteerd!")
            status = "correct"
            aantal_correct += 1
        else:
            print("Foute kleur gedetecteerd!")
            reactietijd = reactietijd + max_tijd  # Straf voor fout
            status = "fout"
            aantal_fout += 1

        colorgame_rondes.append({
            "rondenummer": ronde,
            "waarde": reactietijd,
            "uitkomst": status,
        })

        # Reset the correct cone back to incorrect for clean state
        await device_manager.reset_correct_kegel(gekozen_kleur)

    # Stop polling after all rounds are done
    await device_manager.stop_alle()

    # Clear callback after game
    device_manager.zet_detectie_callback(None)
    await sio.emit('game_einde', {"status":"game gedaan"})
    await asyncio.sleep(0)  # Yield to flush socket
    return colorgame_rondes

async def memorygame(snelheid, aantal_rondes, kleuren):
    geheugen_lijst = []
    rondes_memory = []
    
    for ronde in range(1, aantal_rondes + 1):
        nieuwe_kleur = random.choice(kleuren)
        geheugen_lijst.append(nieuwe_kleur)
        await sio.emit('ronde_start', {'rondenummer': ronde, 'maxronden': aantal_rondes})

        # even wachten met starten
        await asyncio.sleep(3)
        await sio.emit('wacht_even', {'bericht': 'start'})
        
        for kleur in geheugen_lijst:
            await sio.emit('toon_kleur', {'kleur': kleur.upper()})
            print(kleur)
            await asyncio.sleep(snelheid)

        await sio.emit('kleuren_getoond', {'aantal': len(geheugen_lijst)})
        print("Kleuren getoond, wacht op invoer")

        starttijd = time.time()
        status = "correct"
        for kleur in geheugen_lijst:
            invoer = input("Welke kleur werd gedetecteerd? ").strip().lower()
            if invoer != kleur:
                await sio.emit('fout_kleur', {'status': 'game over'})
                status = "fout"
                break
            print("Correct")

        eindtijd = time.time()
        reactietijd = round(eindtijd - starttijd, 2)
        await sio.emit('ronde_einde', {'ronde': ronde, 'status': status})
        print(f"Ronde {ronde} klaar: {status}")
        
        rondes_memory.append({
            'rondenummer': ronde, 
            'reactietijd': reactietijd,
            'status': status
        })
        
        if status == "fout":
            break
            
    await sio.emit('game_einde', {"status":"game gedaan"})
    print("Einde memory game")
    return rondes_memory

@app.post("/games/{game_id}/instellingen",response_model=Instellingen, summary="Haal de instellingen op voor een specifiek spel",tags=["Spelletjes"])
async def get_game_instellingen (json: Instellingen):
    #alles vanuit de json globaal zetten zodat ik die in de andere functie kan gebruiken
    global game_id, gebruikersnaam, moeilijkheids_id, snelheid, ronde_id, rondes, kleuren, starttijd
    
    print(f"Ontvangen instellingen: {json}")

    game_id = json.game_id 
    gebruikersnaam = json.gebruikersnaam
    moeilijkheids_id = json.moeilijkheids_id
    snelheid = json.snelheid
    ronde_id = json.ronde_id
    rondes = json.rondes
    kleuren = json.kleuren

    starttijd = datetime.datetime.now()
    return json


async def run_colorgame_background():
    """Draait het colorgame in de achtergrond en stuurt resultaten via Socket.IO"""
    global game_id, gebruikersnaam, moeilijkheids_id, snelheid, ronde_id, rondes, kleuren, starttijd
    
    try:
        colorgame_rondes = await colorgame(rondes, kleuren, snelheid)
        
        newuserid = DataRepository.add_gebruiker(gebruikersnaam)
        print(f"Nieuwe gebruiker toegevoegd met ID: {newuserid}")

        # Voeg training toe
        training_id = DataRepository.add_training(
            Training(
            start_tijd=starttijd.isoformat(),
            aantal_kleuren=len(kleuren),
            gebruikers_id=newuserid,
            ronde_id=ronde_id,
            moeilijkheids_id=moeilijkheids_id,
            game_id=game_id
            )
        )
        print(f"Nieuwe training toegevoegd met ID: {training_id}")
        # Database opslag
        for ronde in colorgame_rondes:
            DataRepository.add_ronde_waarde(
                RondeWaarde(
                trainings_id=training_id,
                ronde_nummer=ronde["rondenummer"],
                waarde=ronde["waarde"],
                uitkomst=ronde["uitkomst"]
                )
            )
        
    except Exception as e:
        print(f"Fout in colorgame: {e}")
        await sio.emit('game_error', {"error": str(e)})

async def run_memorygame_background():
    """Draait het memorygame in de achtergrond en stuurt resultaten via Socket.IO"""
    global game_id, gebruikersnaam, moeilijkheids_id, snelheid, ronde_id, rondes, kleuren, starttijd
    
    try:
        memorygame_rondes = await memorygame(snelheid, rondes, kleuren)
        
        newuserid = DataRepository.add_gebruiker(gebruikersnaam)
        print(f"Nieuwe gebruiker toegevoegd met ID: {newuserid}")

        # Voeg training toe
        training_id = DataRepository.add_training(
            Training(
            start_tijd=starttijd.isoformat(),
            aantal_kleuren=len(kleuren),
            gebruikers_id=newuserid,
            ronde_id=ronde_id,
            moeilijkheids_id=moeilijkheids_id,
            game_id=game_id
            )
        )
        print(f"Nieuwe training toegevoegd met ID: {training_id}")
        # Database opslag
        for ronde in memorygame_rondes:
            DataRepository.add_ronde_waarde(
                RondeWaarde(
                trainings_id=training_id,
                ronde_nummer=ronde["rondenummer"],
                waarde=ronde["reactietijd"],
                uitkomst=ronde["status"]
                )
            )
        
    except Exception as e:
        print(f"Fout in memorygame: {e}")
        await sio.emit('game_error', {"error": str(e)})

#play game endpoint 
@app.get("/games/{game_id}/play")
async def play_game(background_tasks: BackgroundTasks, game_id: int):
    # Start het spel in de achtergrond
    if(game_id == 1):
        background_tasks.add_task(run_colorgame_background)
    if(game_id == 2):
        background_tasks.add_task(run_memorygame_background)
    
    # Geef direct een response terug
    return {
        "status": "started",
        "message": "Game is gestart, luister naar 'gekozen_kleur' en 'game_finished' events via Socket.IO"
    }

#resulaten endpoint
@app.get("/laatste_rondewaarden",)
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
    if(game_id ==1):
        ranking = DataRepository.get_ranking_for_onetraining(last_training_id)
        return Resultaat(
        game_id=game_id or 0,
        gebruikersnaam=gebruikersnaam or "",
        ranking=ranking or 0,
        gemiddelde_waarde=round(gemiddelde_tijd, 2),
        beste_waarde=round(beste_tijd, 2),
        exactheid=round(exactheid, 0),
        aantal_correct=aantal_correct,
        aantal_fout=aantal_fout,
        aantal_telaat=aantal_telaat,
        correcte_rondewaarden=correcte_rondewaarden_data
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
        correcte_rondewaarden=correcte_rondewaarden_data_memory,
        aantal_correct=aantal_correct_memory,
        aantal_fout=aantal_fout_memory,
        aantal_rondes_niet_gespeeld=aantal_rondes_niet_gespeeld
    )

#games overview endpoint
@app.get("/games/overview", response_model=list[GameVoorOverzicht], summary="Haal een overzicht op van alle spellen met hun highscores", tags=["Spelletjes"])
async def get_games_overview():
    games = DataRepository.get_all_games()
    
    result = []
    for game in games:
        game_id = game['GameId']
        
        # GameId 1 = Color Sprint: laagste gemiddelde tijd van rondewaarden
        # GameId 2+ = Memory etc: hoogste aantal kleuren gebruikt
        if game_id == 1:
            highscore = DataRepository.get_best_avg_for_game(game_id, use_min=True)
        else:
            highscore = DataRepository.get_max_kleuren_for_game(game_id)
        
        result.append(GameVoorOverzicht(
            game_naam=game['GameNaam'],
            tag=game['Tag'],
            highscore=round(highscore, 2),
            eenheid=game['Eenheid']
        ))
    
    return result

@app.get("/games/{game_id}/details", response_model=DetailGame, summary="Haal de details op voor een specifiek spel", tags=["Spelletjes"])
async def get_game_details(game_id: int):
    details = DataRepository.get_game_details(game_id)
    return details


#historie endpoint ----------------------------------------------
@app.get("/games/filters", response_model=list[GameVoorFilter], summary="Haal de lijst van spellen op voor filterdoeleinden", tags=["Spelletjes"])
async def get_games_for_filter():
    games = DataRepository.get_games_for_filter()
    return games

@app.get("/trainingen/historie/{game_id}", response_model=list[TrainingVoorHistorie], summary="Haal de trainingshistorie op voor een gebruiker", tags=["Spelletjes"])
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

@app.get("/trainingen/{training_id}/details", response_model=Union[RondeWaardenVoorDetails, StatistiekenVoorMemoryGame], summary="Haal de details op voor een specifieke training", tags=["Spelletjes"])
async def get_training_details(training_id: int):
    rondewaarden = DataRepository.get_allerondewaarden_by_trainingsId(training_id)
    game_id = DataRepository.get_gameid_by_trainingid(training_id)
    gebruikersnaam = DataRepository.get_gebruikersnaam_by_trainingid(training_id)

    if(game_id==1):
        return RondeWaardenVoorDetails(
        game_id=game_id or 0,
        gebruikersnaam=gebruikersnaam or "",
        gemmidelde_waarde=round(sum(float(item.waarde) for item in rondewaarden) / len(rondewaarden), 2) if rondewaarden else 0,
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



#leaderboard endpoint --------------------------------
@app.get("/games/{game_id}/leaderboard/{max}", response_model=list[LeaderboardItem], summary="Haal de leaderboard op voor een specifiek spel", tags=["Spelletjes"])
async def get_leaderboard(game_id: int, max: int):
    leaderboard = DataRepository.get_leaderboard_for_game(game_id, max)
    return leaderboard


@app.get("/leaderboard/filters/{game_id}", response_model=list[MoeilijkheidVoorLeaderboard], summary="Haal de lijst van spellen op voor filterdoeleinden in de leaderboard", tags=["Spelletjes"])
async def get_moeilijkheden_for_filter(game_id: int):
    moeilijkheden = DataRepository.get_moeilijkheden_for_game(game_id)
    return moeilijkheden


@app.get("/leaderboard/overview/{game_id}/{moeilijkheids_id}", response_model=list[LeaderboardItem], summary="Haal een overzicht op van alle spellen met hun highscores voor de leaderboard", tags=["Spelletjes"])
async def get_leaderboard_overview(game_id:int, moeilijkheids_id:int):
    trainingen = DataRepository.get_leaderboard_with_filters(game_id, moeilijkheids_id)
    return trainingen

# Apparaat Endpoints -----------------------------------------------------------
@app.post("/devices/stop-scan", summary="Stop scanning for devices", tags=["Apparaten"])
async def stop_device_scan():
    await device_manager.stop_apparaat_scan()
    return {"status": "stopped"}

@app.get("/devices/status", summary="Get current device status", tags=["Apparaten"])
async def get_device_status():
    return {
        "apparaten": device_manager.verkrijg_apparaten_status(),
        "scan_actief": device_manager._scan_actief,
        "totaal_verwacht": len(device_manager.vertrouwde_macs)
    }

@app.get("/")
async def read_root():
    return {"Hello": "World"}

if __name__ == "__main__":
    uvicorn.run("backend.src.main:sio_app", host="0.0.0.0", port=8000, log_level="info", reload_dirs=["backend"])