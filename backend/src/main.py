import logging
import asyncio
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
from backend.src.services.GameService import GameService
from backend.src.services.game_manager import GameManager
from backend.src.models.models import Instellingen

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

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

sio_app = socketio.ASGIApp(sio, app)

# Game Endpoints
@app.post("/games/{game_id}/instellingen", response_model=Instellingen, tags=["Spelletjes"])
async def get_game_instellingen(json: Instellingen):
    """Sla game instellingen op in GameManager"""
    game_manager.set_instellingen(json)
    return json

@app.get("/games/{game_id}/play", tags=["Spelletjes"])
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

@app.get("/games/stop", tags=["Spelletjes"])
async def stop_game():
    """Stop de actieve game"""
    result = await game_manager.stop_game()
    await device_manager.stop_alle()
    return result

# Apparaat Endpoints
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