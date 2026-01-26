import logging
import asyncio
import signal
import subprocess
import socketio
import uvicorn
import sys
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, project_root)

from backend.src.services.mqtt_client import MQTTDeviceManager
from backend.src.routers.leaderboard_router import router as leaderboard_router
from backend.src.routers.trainingen_router import router as trainingen_router
from backend.src.routers.games_router import router as games_router
from backend.src.routers import devices_router
from backend.src.services.game_service import GameService
from backend.src.services.game_manager import GameManager
from backend.src.models.models import Instellingen, ColorBattleInstellingen, AlgemeneInstellingen

# Configure logging
log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'brainmove.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

HARDWARE_DELAY = float(os.getenv("HARDWARE_DELAY", "0.07"))

# Initialize SocketIO
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    ping_interval=5,
    ping_timeout=3,
    always_connect=True,
)

# Initialize services
device_manager = MQTTDeviceManager(sio=sio)
game_service = GameService(device_manager=device_manager, sio=sio, hardware_delay=HARDWARE_DELAY)
game_manager = GameManager(game_service=game_service, sio=sio)

# Shutdown state
_should_poweroff = False

def trigger_shutdown():
    global _should_poweroff
    _should_poweroff = True
    os.kill(os.getpid(), signal.SIGTERM)

# Inject dependencies
devices_router.set_device_manager(device_manager)
devices_router.set_shutdown_callback(trigger_shutdown)

@asynccontextmanager
async def lifespan(app: FastAPI):
    mqtt_task = asyncio.create_task(device_manager.start())
    yield
    await device_manager.stop()
    mqtt_task.cancel()

    # Poweroff after cleanup if requested
    if _should_poweroff:
        logger.info("Lifespan cleanup complete, powering off...")
        subprocess.run(["sudo", "poweroff"])

app = FastAPI(
    lifespan=lifespan,
    title="BrainMove API",
    description="""
## BrainMove - Interactieve Bewegingsspellen API

Deze API beheert alle functionaliteit voor het BrainMove systeem, inclusief:

* **Spellen** - Beheer van verschillende cognitieve en reactiespellen
* **Trainingen** - Opslaan en ophalen van trainingsresultaten
* **Leaderboards** - Ranglijsten per spel en moeilijkheidsgraad
* **Apparaten** - MQTT-verbindingen met kleurenkegels
* **Multiplayer** - Color Battle 1v1 wedstrijden

### Hardware Integratie
Het systeem communiceert via MQTT met ESP32-gebaseerde kleurenkegels die spelers moeten aanraken.

### Spellen
1. **Color Sprint** - Reageer zo snel mogelijk op kleuren
2. **Memory** - Onthoud en herhaal kleursequenties  
3. **Number Match** - Match nummers met kleuren
4. **Falling Color** - Timing-gebaseerd kleurenspel
5. **Color Battle** - 1-tegen-1 multiplayer duel
    """,
    version="1.0.0",
)

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
app.include_router(devices_router.router)

sio_app = socketio.ASGIApp(sio, app)

# Game Endpoints
@app.post("/games/{game_id}/instellingen", tags=["Games"])
async def get_game_instellingen(json: AlgemeneInstellingen):
    """Sla game instellingen op in GameManager (single-player of multiplayer)"""
    # Voor multiplayer games (game_id 5)
    if json.game_id == 5 and json.speler1_naam and json.speler2_naam:
        colorbattle_json = ColorBattleInstellingen(
            game_id=json.game_id,
            speler1_naam=json.speler1_naam,
            speler2_naam=json.speler2_naam,
            moeilijkheids_id=json.moeilijkheids_id,
            snelheid=json.snelheid,
            ronde_id=json.ronde_id,
            rondes=json.rondes,
            kleuren=json.kleuren
        )
        game_manager.set_colorbattle_instellingen(colorbattle_json)
        return colorbattle_json
    
    # Voor single-player games
    single_json = Instellingen(
        game_id=json.game_id,
        gebruikersnaam=json.gebruikersnaam or "Speler",
        moeilijkheids_id=json.moeilijkheids_id,
        snelheid=json.snelheid,
        ronde_id=json.ronde_id,
        rondes=json.rondes,
        kleuren=json.kleuren
    )
    game_manager.set_instellingen(single_json)
    return single_json

@app.post("/games/colorbattle/instellingen", response_model=ColorBattleInstellingen, tags=["Games"])
async def set_colorbattle_instellingen(json: ColorBattleInstellingen):
    """Sla Color Battle instellingen op (2 spelers)"""
    game_manager.set_colorbattle_instellingen(json)
    return json

@app.get("/games/{game_id}/play", tags=["Games"])
async def play_game(game_id: int):
    """Start een game via GameManager"""
    result = await game_manager.play_game(game_id)
    
    if result.get("status") == "already_running":
        return JSONResponse(
            status_code=409,  # Conflict
            content=result
        )
    
    if result.get("status") == "missing_settings":
        return JSONResponse(
            status_code=400,  # Bad Request
            content=result
        )
    
    if result.get("status") == "error":
        return JSONResponse(
            status_code=400,  # Bad Request
            content=result
        )
    
    return result

@app.get("/games/stop", tags=["Games"])
async def stop_game():
    """Stop de actieve game"""
    result = await game_manager.stop_game()
    await device_manager.stop_alle()
    return result


@app.get("/")
async def read_root():
    return {"BrainMoveG1": "Backend is running"}

if __name__ == "__main__":
    uvicorn.run("backend.src.main:sio_app", host="0.0.0.0", port=8000, log_level="info", reload_dirs=["backend"])