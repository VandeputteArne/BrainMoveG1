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
from contextlib import asynccontextmanager # <--- 1. Toegevoegd

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, project_root)


from backend.src.services.device_manager import DeviceManager
from backend.src.repositories.data_repository import DataRepository
from backend.src.models.models import (
    Instellingen,
    RondeWaarde,
    Resultaat,
    Training,
    CorrecteRondeWaarde
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

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
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

    for ronde_idx in range(aantal_rondes):
        device_manager.verwijder_alle_laatste_detecties()
        ronde = ronde_idx + 1

        gekozen_kleur = random.choice(kleuren).upper()
        await sio.emit('gekozen_kleur', {'rondenummer': ronde, 'maxronden': aantal_rondes, 'kleur': gekozen_kleur})
        print("Frontend socketio:", gekozen_kleur.upper())

        starttijd = time.time()
        await device_manager.start_alle(gekozen_kleur)
        await asyncio.sleep(0.05)
        
        # Capture baseline (stuck sensors)
        baseline_detecties = device_manager.verkrijg_alle_laatste_detecties()
        baseline_apparaten = set(baseline_detecties.keys())
        if baseline_apparaten:
            print(f"Voorgaande detecties genegeerd: {', '.join(baseline_apparaten)}")
        
        # Clear event and detection
        detectie_event.clear()
        detected_device.clear()
        device_manager.verwijder_alle_laatste_detecties()
        
        # Wacht voor detectie (ORIGINELE LOGICA HERSTELD)
        await detectie_event.wait()
        eindtijd = time.time()
        reactietijd = round(eindtijd - starttijd, 2) - HARDWARE_DELAY
                
        await device_manager.stop_alle()
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
        if apparaatkleur.strip().lower() == gekozen_kleur.strip().lower():
            print("Correcte kleur gedetecteerd!")
            status = "correct"
            aantal_correct += 1
        else:
            print("Foute kleur gedetecteerd!")
            status = "fout"
            aantal_fout += 1

        colorgame_rondes.append({
            "rondenummer": ronde,
            "waarde": reactietijd,
            "uitkomst": status,
        })
    
    # Clear callback after game
    device_manager.zet_detectie_callback(None)
    await sio.emit('game_einde', {"status":"game gedaan"})
    return colorgame_rondes

@app.post("/games/{game_id}/instellingen",response_model=Instellingen, summary="Haal de instellingen op voor een specifiek spel",tags=["Spelletjes"])
async def get_game_instellingen (json: Instellingen):
    #alles vanuit de json globaal zetten zodat ik die in de andere functie kan gebruiken
    global game_id, gebruikersnaam, moeilijkheids_id, snelheid, ronde_id, rondes, kleuren, starttijd

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
    
@app.get("/games/{game_id}/play")
async def play_game(background_tasks: BackgroundTasks):
    # Start het spel in de achtergrond
    background_tasks.add_task(run_colorgame_background)
    
    # Geef direct een response terug
    return {
        "status": "started",
        "message": "Game is gestart, luister naar 'gekozen_kleur' en 'game_finished' events via Socket.IO"
    }

@app.get("/laatste_rondewaarden",)
async def get_laatste_rondewaarden():
    list_rondewaarden = DataRepository.get_last_rondewaarden_from_last_training()

    gemiddelde_tijd = list_rondewaarden and sum(float(item.waarde) for item in list_rondewaarden) / len(list_rondewaarden) or 0
    beste_tijd = list_rondewaarden and min(float(item.waarde) for item in list_rondewaarden) or 0

    # Bepaal ID van de laatst toegevoegde training en vraag ranking op
    last_training_id = DataRepository.get_last_training_id()
    ranking = None
    if last_training_id:
        ranking = DataRepository.get_ranking_for_onetraining(last_training_id)
    
    exactheid = len([item for item in list_rondewaarden if item.uitkomst == 'correct']) / len(list_rondewaarden) * 100 if list_rondewaarden else 0

    aantal_correct = len([item for item in list_rondewaarden if item.uitkomst == 'correct'])
    aantal_fout = len([item for item in list_rondewaarden if item.uitkomst == 'fout'])
    aantal_telaat = len([item for item in list_rondewaarden if item.uitkomst == 'te laat'])

    #ophalen welke rondes met hun rondenummers en waardes waar correct voor de grafiek
    correcte_rondewaarden = [item for item in list_rondewaarden if item.uitkomst == 'correct']
    # Hier kun je verdere verwerking van correcte_rondewaarden toevoegen, bijvoorbeeld voor een grafiek
    correcte_rondewaarden_data = [CorrecteRondeWaarde(ronde_nummer=item.ronde_nummer, waarde=item.waarde) for item in correcte_rondewaarden]

    return Resultaat(
        ranking=ranking or 0,
        gemiddelde_waarde=round(gemiddelde_tijd, 2),
        beste_waarde=round(beste_tijd, 2),
        exactheid=exactheid,
        aantal_correct=aantal_correct,
        aantal_fout=aantal_fout,
        aantal_telaat=aantal_telaat,
        correcte_rondewaarden=correcte_rondewaarden_data
    )

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