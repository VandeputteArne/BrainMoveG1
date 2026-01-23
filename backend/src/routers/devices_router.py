import os
from fastapi import APIRouter
from models.models import UitschakelenRequest

router = APIRouter(prefix="/devices", tags=["Apparaten"])

# Deze variabele wordt geïnjecteerd vanuit main.py
device_manager = None
_shutdown_callback = None

def set_device_manager(manager):
    """Inject de device manager dependency"""
    global device_manager
    device_manager = manager

def set_shutdown_callback(callback):
    """Inject shutdown callback to trigger after lifespan cleanup"""
    global _shutdown_callback
    _shutdown_callback = callback

@router.get("/status", summary="Get current device status")
async def get_device_status():
    return {
        "apparaten": device_manager.verkrijg_apparaten_status(),
        "connected": device_manager._connected,
        "totaal_verwacht": 4
    }

@router.post("/uitschakelen", summary="Schakel alle apparaten uit")
async def uitschakelen_apparaten(request: UitschakelenRequest):
    wachtwoord = os.getenv("PI_PASSWORD")
    if(request.inputGebruiker != wachtwoord):
        return {"status": "Foutief wachtwoord, apparaten niet uitgeschakeld"}

    await device_manager.sleep_alle()

    if _shutdown_callback:
        _shutdown_callback()

    return {"status": "Alle apparaten worden uitgeschakeld"}
