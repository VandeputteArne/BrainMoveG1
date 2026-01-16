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
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

# Add project root to path for direct script execution
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

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Maak een Socket.IO server
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
sio_app = socketio.ASGIApp(sio, app)

# Initialize DeviceManager with socket.io reference
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
    # Haal de verbonden apparaten op en sorteer ze op naam voor consistentie
    verbonden_apparaten = sorted(device_manager.apparaten.keys())
    
    # Maak mapping: apparaat_id -> kleur
    # Belangrijk: Dit gaat ervan uit dat je evenveel kleuren hebt als verbonden apparaten
    apparaat_id_mapping = {}
    for idx, apparaat_naam in enumerate(verbonden_apparaten):
        if idx < len(kleuren):
            # Probeer apparaat_id te krijgen - gebruik idx als fallback
            apparaat_id_mapping[idx] = kleuren[idx]
    
    # Fallback: ook mapping maken op basis van ESP naam indien die kleur bevat
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

    for ronde_idx in range(aantal_rondes):
        # Clear previous detections
        device_manager.verwijder_alle_laatste_detecties()
        ronde = ronde_idx + 1

        gekozen_kleur = random.choice(kleuren).upper()
        await sio.emit('gekozen_kleur', {'rondenummer': ronde, 'maxronden': aantal_rondes, 'kleur': gekozen_kleur})
        print("Frontend socketio:", gekozen_kleur.upper())

        # Start polling and immediately capture baseline (pre-existing detections)
        starttijd = time.time()
        await device_manager.start_alle(gekozen_kleur)
        await asyncio.sleep(0.05)  # Brief delay to let initial state settle
        
        # Capture and filter out any pre-existing detections (stuck sensors)
        baseline_detecties = device_manager.verkrijg_alle_laatste_detecties()
        baseline_apparaten = set(baseline_detecties.keys())
        if baseline_apparaten:
            print(f"⚠️  Pre-existing detections ignored: {', '.join(baseline_apparaten)}")
        device_manager.verwijder_alle_laatste_detecties()
        
        # Now wait for a NEW detection (not in baseline)
        esp_dict = {}
        while not esp_dict:
            await asyncio.sleep(0.05)
            alle_detecties = device_manager.verkrijg_alle_laatste_detecties()
            # Only accept detections from devices that weren't already detecting
            esp_dict = {}
            for k, v in alle_detecties.items():
                if k not in baseline_apparaten:
                    esp_dict[k] = v
                
        await device_manager.stop_alle()
        print(esp_dict)

        # Bepaal welke kleur gedetecteerd is
        gedetecteerde_esp_naam = list(esp_dict.keys())[0]  # Eerste (en enige) detectie
        detection = esp_dict[gedetecteerde_esp_naam]
        device_id = detection.get("apparaat_id", None)
        
        eindtijd = time.time()
        reactietijd = round(eindtijd - starttijd, 2)
        rondetijden[ronde] = reactietijd

        if reactietijd > max_tijd:
            print(f"Te laat! Reactietijd: {reactietijd:.2f} seconden")
            aantal_telaat += 1
            colorgame_rondes.append({
                "rondenummer": ronde,
                "waarde": max_tijd,
                "uitkomst": "te laat",
            })
            continue

        # Probeer kleur te bepalen:
        # 1. Eerst via ESP naam (als die de kleur bevat)
        # 2. Anders via apparaat_id mapping
        apparaatkleur = None
        
        # Methode 1: Kleur uit ESP naam
        if gedetecteerde_esp_naam in kleur_mapping:
            apparaatkleur = kleur_mapping[gedetecteerde_esp_naam]
            print(f"Kleur bepaald via naam: {gedetecteerde_esp_naam} -> {apparaatkleur}")
        
        # Methode 2: Kleur via apparaat_id
        elif device_id is not None:
            if isinstance(device_id, str) and device_id.isdigit():
                device_id = int(device_id)
            if isinstance(device_id, int) and device_id in apparaat_id_mapping:
                apparaatkleur = apparaat_id_mapping[device_id]
                print(f"Kleur bepaald via ID: apparaat_id {device_id} -> {apparaatkleur}")

        print(f"Gedetecteerd: ESP={gedetecteerde_esp_naam}, ID={device_id}, Kleur={apparaatkleur}")

        if apparaatkleur is None:
            print(f"⚠️  Fout: Geen kleur gevonden voor {gedetecteerde_esp_naam} (device_id {device_id})")
            aantal_fout += 1
            colorgame_rondes.append({
                "rondenummer": ronde,
                "waarde": reactietijd,
                "uitkomst": "fout",
            })
            continue

        # Vergelijk genormaliseerde strings
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

    await device_manager.scannen(1)
    await device_manager.verbind_alle()
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

@app.get("/")
async def read_root():
    return {"Hello": "World"}


# Apparaat Endpoints -----------------------------------------------------------
@app.post("/api/devices/start-scan", summary="Gestart met scannen", tags=["Apparaten"])
async def start_device_scan(background_tasks: BackgroundTasks):
    background_tasks.add_task(device_manager.start_apparaat_scan)
    return {
        "status": "scanning",
    }


@app.post("/api/devices/stop-scan", summary="Stop scanning for devices", tags=["Apparaten"])
async def stop_device_scan():
    await device_manager.stop_apparaat_scan()
    return {"status": "stopped"}


@app.get("/api/devices/status", summary="Get current device status", tags=["Apparaten"])
async def get_device_status():
    return {
        "apparaten": device_manager.verkrijg_apparaten_status(),
        "scan_actief": device_manager._scan_actief,
        "totaal_verwacht": len(device_manager.vertrouwde_macs)
    }

if __name__ == "__main__":
    uvicorn.run("backend.src.main:sio_app", host="0.0.0.0", port=8000, log_level="info", reload_dirs=["backend"])