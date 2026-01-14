import random
import time
import asyncio
import typing
import logging
from enum import IntEnum
from classes.device_manager import DeviceManager
from classes.esp32_device import ESP32Device
from bleak import BleakClient, BleakScanner

# configureer basic logging zodat logger.info/debug zichtbaar wordt
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


device_manager = DeviceManager()


class KEGELS(IntEnum):
    BLAUW = 0
    ROOD = 1
    GEEL = 2
    GROEN = 3

# Connect to esp
async def colorgame(aantal_rondes, kleuren, snelheid):
    global device_manager
    # maak mapping esp-id -> kleur
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
        
        # Stop all devices and wait for state to clear
        await device_manager.stop_alle()
        await asyncio.sleep(0.3)
        
        # Clear again to remove any lingering detections from the stop command
        device_manager.verwijder_alle_laatste_detecties()

        gekozen_kleur = random.choice(kleuren).upper()
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
        rondetijden[ronde + 1] = reactietijd

        if reactietijd > max_tijd:
            print(f"Te laat! Reactietijd: {reactietijd:.2f} seconden")
            aantal_telaat += 1
            colorgame_rondes.append({
                "rondenummer": ronde + 1,
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
                "rondenummer": ronde + 1,
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
            "rondenummer": ronde + 1,
            "waarde": reactietijd,
            "uitkomst": status,
        })

    return colorgame_rondes

# Endpoint
def endpoint(json):
    spel_id = json.spel_id
    gebruikersnaam = json.gebruikersnaam
    moeilijkheid_id= json.moeilijkheid_id
    ronde_id = json.ronde_id
    # bvb 1, linked aan 10 rondes in db
    aantal_kleuren = len(json.kleuren)

    snelheid = json.snelheid
    aantal_rondes = json.aantal_rondes
    kleuren = json.kleuren

    colorgame_rondes = colorgame(aantal_rondes, kleuren, snelheid)
    # colorgame_rondes = [{rondenummer: 1, waarde: sec, uitkomst: status}, {...}, {...}]

    # gebruiker_id = maak_gebruiker(gebruikersnaam)

    # training_id = SendToDatabase(start_tijd, aantal_kleuren, gebruiker_id, ronde_id, moeilijkheid_id, spel_id)
    
    # dict_rondes = {}
    # rondes[training_id] = training_id
    # For ronde in colorgame_rondes:
    # dict_rondes.rondes.append({})



async def main():
    await device_manager.scannen(2)
    await device_manager.verbind_alle()

    colorgames_rondes = await colorgame(5, ['blauw', 'rood', 'geel', 'groen'], 5.0)

    # Id's van database
    # gebruiker_id = 1
    # training_id = 1

    # # Voor database
    # dict_rondewaarden = {}
    # dict_rondewaarden[training_id] = training_id

        # Open connection
        # Start transaction
    for ronde in colorgames_rondes:
        rondenummer = ronde["rondenummer"]
        waarde = ronde["waarde"]
        uitkomst = ronde["uitkomst"]
        # InsertIntoDatabase(colorgames_rondes.training_id, rondenummer, waarde, uitkomst, training_id)
        print(f"Invoegen ronde {rondenummer}: waarde={waarde} seconden, uitkomst={uitkomst}")

asyncio.run(main())