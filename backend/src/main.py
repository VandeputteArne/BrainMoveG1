import asyncio
import datetime
import threading
import fastapi
import socketio
import uvicorn
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from models.models import (
    Instellingen,
    RondeWaarde,
    Resultaat,
)
from backend.src.services.device_manager import DeviceManager
import random
import time
from DataRepository import DataRepository

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
device_manager = DeviceManager()

# Maak een Socket.IO server
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
sio_app = socketio.ASGIApp(sio, app)

global game_id
global gebruikersnaam
global moeilijkheids_id
global snelheid
global ronde_id
global rondes
global kleuren

global starttijd


async def colorgame(aantal_rondes, kleuren, snelheid):
    # maak mapping esp-id -> kleur
    global vorige_kleur
    apparaten = {i: kleuren[i] for i in range(len(kleuren))}
    
    colorgame_rondes = []

    aantal_correct = 0
    aantal_fout = 0
    aantal_telaat = 0
    rondetijden = {}

    max_tijd = float(snelheid)

    for ronde in range(aantal_rondes):
        # Clear previous detections
        device_manager.verwijder_alle_laatste_detecties()
        ronde = ronde+1
        
        # Stop all devices and wait for state to clear
        #await device_manager.stop_alle()
        #await asyncio.sleep(0.1)
        
        # Clear again to remove any lingering detections from the stop command
        #device_manager.verwijder_alle_laatste_detecties()

        gekozen_kleur = random.choice(kleuren).upper()
        await sio.emit('gekozen_kleur', {'rondenummer': ronde, 'maxronden': aantal_rondes, 'kleur': gekozen_kleur})
        print("Frontend socketio:", gekozen_kleur.upper())

        # Start polling and immediately capture baseline (pre-existing detections)
        starttijd = time.time()
        await device_manager.start_alle(gekozen_kleur)
        await asyncio.sleep(0.2)  # Brief delay to let initial state settle
        
        # Capture and filter out any pre-existing detections (stuck sensors)
        baseline_detecties = device_manager.verkrijg_alle_laatste_detecties()
        baseline_apparaten = set(baseline_detecties.keys())
        if baseline_apparaten:
            print(f"⚠️  Pre-existing detections ignored: {', '.join(baseline_apparaten)}")
        device_manager.verwijder_alle_laatste_detecties()
        
        # Now wait for a NEW detection (not in baseline)
        esp_dict = {}
        while not esp_dict:
            await asyncio.sleep(0.1)
            alle_detecties = device_manager.verkrijg_alle_laatste_detecties()
            # Only accept detections from devices that weren't already detecting
            esp_dict = {}
            for k, v in alle_detecties.items():
                if k not in baseline_apparaten:
                    esp_dict[k] = v
                
        await device_manager.stop_alle()
        print(esp_dict)

        gedetecteerde_esp_id = None

        for esp_name, detection in esp_dict.items():
            device_id = detection.get("apparaat_id", None)
            if isinstance(device_id, int):
                gedetecteerde_esp_id = device_id
                break

            if isinstance(device_id, str) and device_id.isdigit():
                gedetecteerde_esp_id = int(device_id)
                break

            suffix = esp_name.split('-')[-1]
            if suffix.isdigit():
                gedetecteerde_esp_id = int(suffix)
                break

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

        esp_lookup_id = gedetecteerde_esp_id
        apparaatkleur = apparaten.get(esp_lookup_id)

        print(f"Gedetecteerde kleur is: {apparaatkleur} (device_id {gedetecteerde_esp_id} -> key {esp_lookup_id})")

        if apparaatkleur is None:
            print(f"Fout: Geen kleur gevonden voor device_id {gedetecteerde_esp_id}")
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
            starttijd=starttijd,
            aantalKleuren=len(kleuren),
            gebruikersId=newuserid,
            rondeId=ronde_id,
            moeilijkheidsId=moeilijkheids_id,
            gameId=game_id
        )
        print(f"Nieuwe training toegevoegd met ID: {training_id}")
        # Database opslag
        for ronde in colorgame_rondes:
            DataRepository.add_ronde_waarde(
                trainingsId=training_id,
                rondeNummer=ronde["rondenummer"],
                waarde=ronde["waarde"],
                uitkomst=ronde["uitkomst"]
            )
            
        
        
    except Exception as e:
        print(f"Fout in colorgame: {e}")
        await sio.emit('game_error', {"error": str(e)})

    
@app.get("/games/{game_id}/play")
async def play_game(background_tasks: BackgroundTasks):
    # Start het spel in de achtergrond
    await asyncio.sleep(0.5)  # Kleine vertraging om ervoor te zorgen dat de response wordt teruggestuurd voordat de taak begint
    background_tasks.add_task(run_colorgame_background)
    
    # Geef direct een response terug
    return {
        "status": "started",
        "message": "Game is gestart, luister naar 'gekozen_kleur' en 'game_finished' events via Socket.IO"
    }

@app.get("/laatste_rondewaarden",)
async def get_laatste_rondewaarden():
    list_rondewaarden = DataRepository.get_last_rondewaarden_from_last_training()

    gemiddelde_tijd = list_rondewaarden and sum(float(item['Waarde']) for item in list_rondewaarden) / len(list_rondewaarden) or 0
    beste_tijd = list_rondewaarden and min(float(item['Waarde']) for item in list_rondewaarden) or 0

    # Bepaal ID van de laatst toegevoegde training en vraag ranking op
    last_training_id = DataRepository.get_last_training_id()
    ranking = None
    if last_training_id:
        ranking = DataRepository.get_ranking_for_onetraining(last_training_id)
    
    exactheid = len([item for item in list_rondewaarden if item['Uitkomst'] == 'correct']) / len(list_rondewaarden) * 100 if list_rondewaarden else 0

    aantal_correct = len([item for item in list_rondewaarden if item['Uitkomst'] == 'correct'])
    aantal_fout = len([item for item in list_rondewaarden if item['Uitkomst'] == 'fout'])
    aantal_telaat = len([item for item in list_rondewaarden if item['Uitkomst'] == 'te laat'])

    return Resultaat(
        ranking=ranking or 0,
        gemiddelde_waarde=round(gemiddelde_tijd, 2),
        beste_waarde=round(beste_tijd, 2),
        exactheid=exactheid,
        aantal_correct=aantal_correct,
        aantal_fout=aantal_fout,
        aantal_telaat=aantal_telaat
    )

@app.get("/")
async def read_root():
    return {"Hello": "World"}

if __name__ == "__main__":
    
    uvicorn.run("main:sio_app", host="0.0.0.0", port=8000, log_level="info", reload_dirs=["backend"])