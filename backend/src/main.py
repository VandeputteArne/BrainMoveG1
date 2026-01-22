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



from backend.src.services.mqtt_client import MQTTDeviceManager
from backend.src.repositories.data_repository import DataRepository

from backend.src.routers.leaderboard_router import router as leaderboard_router
from backend.src.routers.trainingen_router import router as trainingen_router
from backend.src.routers.games_router import router as games_router

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
    StatistiekenVoorMemoryGame,
    StatistiekenVoorColorSprint,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

@asynccontextmanager
async def lifespan(app: FastAPI):
    mqtt_task = asyncio.create_task(device_manager.start())

    yield

    await device_manager.stop()
    mqtt_task.cancel()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(leaderboard_router)
app.include_router(trainingen_router)
app.include_router(games_router)
HARDWARE_DELAY = float(os.getenv("HARDWARE_DELAY", "0.07"))

sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    ping_interval=5,
    ping_timeout=3,
    always_connect=True,
)
sio_app = socketio.ASGIApp(sio, app)
device_manager = MQTTDeviceManager(sio=sio)

global game_id
global gebruikersnaam
global moeilijkheids_id
global snelheid
global ronde_id
global rondes
global kleuren
global starttijd

# Game control variabelen
current_game_task = None
game_stop_event = asyncio.Event()

async def colorgame(aantal_rondes, kleuren, snelheid):
    colorgame_rondes = []
    aantal_correct = 0
    aantal_fout = 0
    aantal_telaat = 0

    max_tijd = float(snelheid)

    detectie_event = asyncio.Event()
    detected_color = {}

    def on_detectie(gebeurtenis):
        detected_color.clear()
        detected_color.update(gebeurtenis)
        detectie_event.set()

    device_manager.zet_detectie_callback(on_detectie)

    await device_manager.start_alle()

    for ronde in range(1, aantal_rondes + 1):
        # Check of de game gestopt moet worden
        if game_stop_event.is_set():
            print("Game gestopt door gebruiker")
            break
            
        gekozen_kleur = random.choice(kleuren).upper()

        # Emit to frontend
        await sio.emit('gekozen_kleur', {
            'rondenummer': ronde,
            'maxronden': aantal_rondes,
            'kleur': gekozen_kleur
        })
        print(f"Round {ronde}: Chosen color = {gekozen_kleur}")

        # Kleine delay zodat frontend de kleur kan tonen
        await asyncio.sleep(0.2)

        await device_manager.set_correct_kegel(gekozen_kleur)

        detectie_event.clear()
        detected_color.clear()
        starttijd = time.time()

        try:
            # Wacht op detectie OF stop event
            detectie_task = asyncio.create_task(detectie_event.wait())
            stop_task = asyncio.create_task(game_stop_event.wait())
            
            done, pending = await asyncio.wait(
                [detectie_task, stop_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel pending tasks
            for task in pending:
                task.cancel()
            
            # Check of game gestopt is
            if stop_task in done:
                print("Game gestopt tijdens wachten op detectie")
                break
            
            # Anders is detectie gebeurd
            if detectie_task in done:
                reactietijd = round(time.time() - starttijd, 2) - HARDWARE_DELAY

                detected_kleur = detected_color.get("kleur", "").lower()
                if(max_tijd - reactietijd) < 0:
                    # Te laat
                    reactietijd = max_tijd
                    status = "te laat"
                    aantal_telaat += 1
                    print(f"Too late! Reaction time: {reactietijd}s")
                elif detected_kleur == gekozen_kleur.lower():
                    status = "correct"
                    aantal_correct += 1
                    print(f"Correct! Reaction time: {reactietijd}s")
                else:
                    status = "fout"
                    aantal_fout += 1
                    reactietijd += max_tijd  # Penalty
                    print(f"Wrong color! Detected: {detected_kleur}, Expected: {gekozen_kleur}")
            else:
                # Timeout
                reactietijd = max_tijd
                status = "te laat"
                aantal_telaat += 1
                print(f"Too late! Timeout after {max_tijd}s")

        except Exception as e:
            print(f"Error in colorgame ronde: {e}")
            reactietijd = max_tijd
            status = "fout"

        colorgame_rondes.append({
            "rondenummer": ronde,
            "waarde": reactietijd,
            "uitkomst": status,
        })

        await device_manager.reset_correct_kegel(gekozen_kleur)

    await device_manager.stop_alle()

    device_manager.zet_detectie_callback(None)
    await sio.emit('game_einde', {"status":"game gedaan"})
    return colorgame_rondes

async def memorygame(snelheid, aantal_rondes, kleuren):
    geheugen_lijst = []
    rondes_memory = []

    detectie_event = asyncio.Event()
    detected_color = {}

    def on_detectie(gebeurtenis):
        detected_color.clear()
        detected_color.update(gebeurtenis)
        detectie_event.set()

    device_manager.zet_detectie_callback(on_detectie)

    

    for ronde in range(1, aantal_rondes + 1):
        # Check of de game gestopt moet worden
        if game_stop_event.is_set():
            print("Game gestopt door gebruiker")
            break
            
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
        await device_manager.start_alle()

        starttijd = time.time()
        status = "correct"

        # for verwachte_kleur in geheugen_lijst:
        #     detectie_event.clear()
        #     detected_color.clear()

        #     try:
        #         # Wait for detection with generous timeout
        #         await asyncio.wait_for(detectie_event.wait(), timeout=30.0)

        #         detected_kleur = detected_color.get("kleur", "").lower()
        #         if detected_kleur != verwachte_kleur.lower():
        #             await sio.emit('fout_kleur', {'status': 'game over'})
        #             status = "fout"
        #             print(f"Wrong! Expected {verwachte_kleur}, got {detected_kleur}")
        #             break
        #         print(f"Correct: {detected_kleur}")

        #     except asyncio.TimeoutError:
        #         await sio.emit('fout_kleur', {'status': 'timeout'})
        #         status = "fout"
        #         print("Timeout waiting for cone touch")
        #         break

        for verwachte_kleur in geheugen_lijst:
            # Check stop event ook tussen detecties
            if game_stop_event.is_set():
                print("Game gestopt tijdens memory sequence")
                status = "gestopt"
                break
            
            detectie_event.clear()
            detected_color.clear()

            await device_manager.set_correct_kegel(verwachte_kleur)

            try:
                # Wacht op detectie OF stop event
                detectie_task = asyncio.create_task(detectie_event.wait())
                stop_task = asyncio.create_task(game_stop_event.wait())
                
                done, pending = await asyncio.wait(
                    [detectie_task, stop_task],
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # Cancel pending tasks
                for task in pending:
                    task.cancel()
                
                await device_manager.reset_correct_kegel(verwachte_kleur)
                
                # Check of game gestopt is
                if stop_task in done:
                    print("Game gestopt tijdens wachten op aanraking")
                    status = "gestopt"
                    break
                
                # Check of detectie gebeurd is
                if detectie_task in done:
                    detected_kleur = detected_color.get("kleur", "").lower()
                    
                    if detected_kleur != verwachte_kleur.lower():
                        await sio.emit('fout_kleur', {'status': 'game over'})
                        status = "fout"
                        print(f"Fout! Verwacht: {verwachte_kleur}, Gekregen: {detected_kleur}")
                        break
                    
                    print(f"Correct: {detected_kleur}")
                else:
                    # Timeout
                    await sio.emit('fout_kleur', {'status': 'timeout'})
                    status = "fout"
                    print("Timeout: Te lang gewacht op aanraking")
                    break

            except Exception as e:
                await device_manager.reset_correct_kegel(verwachte_kleur)
                print(f"Error in memory sequence: {e}")
                status = "fout"
                break

        eindtijd = time.time()
        reactietijd = round(eindtijd - starttijd, 2)
        await sio.emit('ronde_einde', {'ronde': ronde, 'status': status})
        print(f"Ronde {ronde} klaar: {status}")
        await device_manager.stop_alle()

        rondes_memory.append({
            'rondenummer': ronde,
            'reactietijd': reactietijd,
            'status': status
        })

        if status == "fout":
            break

    

    device_manager.zet_detectie_callback(None)
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
    global current_game_task, game_stop_event
    
    try:
        # Reset stop event aan het begin van een nieuwe game
        game_stop_event.clear()
        
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
    global current_game_task, game_stop_event
    
    try:
        # Reset stop event aan het begin van een nieuwe game
        game_stop_event.clear()
        
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
async def play_game(game_id: int):
    global current_game_task, game_stop_event
    
    # Check of er al een game actief is
    if current_game_task and not current_game_task.done():
        return {
            "status": "already_running",
            "message": "Er is al een game actief. Stop deze eerst voordat je een nieuwe start."
        }
    
    # Start het spel in de achtergrond
    if game_id == 1:
        current_game_task = asyncio.create_task(run_colorgame_background())
    elif game_id == 2:
        current_game_task = asyncio.create_task(run_memorygame_background())
    else:
        return {
            "status": "error",
            "message": f"Onbekend game_id: {game_id}"
        }
    
    # Geef direct een response terug
    return {
        "status": "started",
        "message": "Game is gestart, luister naar 'gekozen_kleur' en 'game_finished' events via Socket.IO"
    }

@app.get("/games/stop")
async def stop_game():
    global current_game_task, game_stop_event
    
    if current_game_task is None or current_game_task.done():
        return {
            "status": "no_game_running",
            "message": "Er is geen actieve game om te stoppen"
        }
    
    # Zet stop event om game loops te laten stoppen
    game_stop_event.set()
    
    # Cancel de achtergrond task
    current_game_task.cancel()
    
    try:
        await current_game_task
    except asyncio.CancelledError:
        print("Game task succesvol geannuleerd")
    
    # Stop alle apparaten
    await device_manager.stop_alle()



#resulaten endpoint






# Apparaat Endpoints -----------------------------------------------------------

@app.get("/devices/status", summary="Get current device status", tags=["Apparaten"])
async def get_device_status():
    return {
        "apparaten": device_manager.verkrijg_apparaten_status(),
        "connected": device_manager._connected,
        "totaal_verwacht": 4
    }

@app.get("/")
async def read_root():
    return {"Hello": "World"}

if __name__ == "__main__":
    uvicorn.run("backend.src.main:sio_app", host="0.0.0.0", port=8000, log_level="info", reload_dirs=["backend"])