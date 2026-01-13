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
logger.setLevel(logging.WARNING)


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

    # gebruik de snelheid-parameter als max tijd
    max_tijd = float(snelheid)

    for ronde in range(aantal_rondes):
        device_manager.remove_all_last_detections()

        gekozen_kleur = random.choice(kleuren).upper()
        gekozen_kegel_id = KEGELS[gekozen_kleur]

        # Sturen naar frontend via socketio
        print("Frontend socketio:", gekozen_kleur.upper())

        # Start polling esp en meet reactietijd
        starttijd = time.time()
        await device_manager.start_all(gekozen_kegel_id)
        esp_dict = device_manager.get_all_last_detections()
        while not esp_dict:
            await asyncio.sleep(0.1)
            esp_dict = device_manager.get_all_last_detections()
        await device_manager.stop_all()

        print(esp_dict)

        # Zoek eerste detectie-event en haal device_id op zonder zware excepts
        gedetecteerde_esp_id = None

        for esp_name, detection in esp_dict.items():
            # Als device_id een int is, gebruik het direct
            device_id = getattr(detection, "device_id", None)
            if isinstance(device_id, int):
                gedetecteerde_esp_id = device_id
                break
            # Als device_id een string met cijfers is, parse die
            if isinstance(device_id, str) and device_id.isdigit():
                gedetecteerde_esp_id = int(device_id)
                break
            # fallback: parse het nummer uit esp_name (bijv. 'BM-3') als het cijfer is
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
    await device_manager.scan()
    await device_manager.connect_all()

    colorgames_rondes = await colorgame(5, ['blauw', 'rood', 'geel', 'groen'], 2.0)

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