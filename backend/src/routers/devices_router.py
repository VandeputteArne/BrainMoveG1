from fastapi import APIRouter

router = APIRouter(prefix="/devices", tags=["Apparaten"])

# Deze variabele wordt geïnjecteerd vanuit main.py
device_manager = None

def set_device_manager(manager):
    """Inject de device manager dependency"""
    global device_manager
    device_manager = manager

@router.get("/status", summary="Get current device status")
async def get_device_status():
    return {
        "apparaten": device_manager.verkrijg_apparaten_status(),
        "connected": device_manager._connected,
        "totaal_verwacht": 4
    }

@router.get("/uitschakelen", summary="Schakel alle apparaten uit")
async def uitschakelen_apparaten():
    print("Uitschakelen alle apparaten via endpoint")
    return {"status": "Alle apparaten zijn uitgeschakeld"}
