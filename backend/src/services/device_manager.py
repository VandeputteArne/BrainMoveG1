import logging
import os
from typing import Optional, Dict, List
from bleak import BleakScanner
from dotenv import load_dotenv
from esp32_device import (
    ESP32Device,
    DetectieCallback,
    BatterijCallback,
    StatusCallback,
    APPARAAT_PREFIX
)

# Logging------------------------------------------------------------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# DeviceManager class------------------------------------------------
class DeviceManager:
    def __init__(self) -> None:
        
        self._apparaten: Dict[str, ESP32Device] = {}
        
        load_dotenv()
        self.veiligheids_byte = int(os.getenv("VEILIGHEIDS_BYTE", "0x42"), 0)
        self.scan_timeout = float(os.getenv("SCAN_TIMEOUT", "5.0"))
        self.verbindings_timeout = float(os.getenv("VERBINDING_TIMEOUT", "10.0"))
        self._strikte_whitelist = os.getenv("STRIKTE_WHITELIST", "").lower() == "true"
        self._vertrouwde_macs = {}
        for kleur in ("BLAUW", "ROOD", "GEEL", "GROEN"):
            mac = os.getenv(f"APPARAAT_BM_{kleur}")
            if mac:
                self._vertrouwde_macs[mac] = f"BM-{kleur.capitalize()}"
        
        self._detectie_callback: Optional[DetectieCallback] = None
        self._batterij_callback: Optional[BatterijCallback] = None
        self._status_callback: Optional[StatusCallback] = None

        self._laatste_detecties: Dict[str, dict] = {}
    

    # Eigenschappen----------------------------------------------------------------------
    @property
    def apparaten(self) -> Dict[str, ESP32Device]:
        return self._apparaten.copy()
    

    @property
    def vertrouwde_macs(self) -> Dict[str, str]:
        return self._vertrouwde_macs.copy()
    
    
    @property
    def strikte_whitelist(self) -> bool:
        return self._strikte_whitelist
    

    # Methoden--------------------------------------------------------------------------    
    # Nog te bekijken
    def _bind_detectie_aan_apparaat(self, apparaat: ESP32Device) -> None:
        def _wrapper(gebeurtenis: dict):
            try:
                self._laatste_detecties[apparaat.naam] = gebeurtenis
            except Exception:
                logger.exception(f"Mislukt detectie opslaan voor {apparaat.naam}")
            
            if self._detectie_callback:
                try:
                    self._detectie_callback(gebeurtenis)
                except Exception:
                    logger.exception(f"Detectie callback wierp fout voor {apparaat.naam}")
        
        apparaat.bij_detectie = _wrapper


    def _voeg_apparaat_toe(self, apparaat: ESP32Device) -> None:
        self._bind_detectie_aan_apparaat(apparaat)

        if self._batterij_callback:
            apparaat.bij_batterij = self._batterij_callback

        if self._status_callback:
            apparaat.bij_status = self._status_callback
        
        self._apparaten[apparaat.naam] = apparaat
        logger.info(f"Apparaat toegevoegd: {apparaat.naam}")


    async def scannen(self, max_pogingen: int = 10) -> List[ESP32Device]:
        scan_timeout = self.scan_timeout
        logger.info(f"Scannen BM apparaten")
        
        if self._strikte_whitelist:
            logger.info("MAC whitelist INGESCHAKELD")
        
        totaal_apparaten_nodig = len(self._vertrouwde_macs)
        nieuwe_apparaten = []
        pogingen = 0
        
        while pogingen < max_pogingen:
            pogingen += 1
            
            vertrouwd = {m.upper() for m in self._vertrouwde_macs.keys()}
            vertrouwde_gevonden = 0
            for apparaat in self._apparaten.values():
                if apparaat.mac_adres.upper() in vertrouwd:
                    vertrouwde_gevonden += 1

            if vertrouwde_gevonden >= totaal_apparaten_nodig and totaal_apparaten_nodig > 0:
                logger.info(f"Alle {totaal_apparaten_nodig} vertrouwde apparaten gevonden!")
                break
            
            logger.info(f"Scan poging {pogingen}/{max_pogingen} - Gevonden {vertrouwde_gevonden}/{totaal_apparaten_nodig} vertrouwde apparaten")
            
            ontdekt = await BleakScanner.discover(timeout=scan_timeout)
            
            for ble_apparaat in ontdekt:
                if not ble_apparaat.name or not ble_apparaat.name.startswith(APPARAAT_PREFIX):
                    continue
                
                mac = ble_apparaat.address
                naam = ble_apparaat.name
                
                if self._strikte_whitelist:
                    if mac.upper() not in [m.upper() for m in self._vertrouwde_macs.keys()]:
                        logger.warning(f"AFGEWEZEN: {naam} ({mac}) - niet in whitelist")
                        continue
                    
                    verwachte_naam = self._vertrouwde_macs.get(mac.upper())
                    if verwachte_naam and verwachte_naam != naam:
                        logger.warning(f"BEVEILIGING: {mac} adverteert als '{naam}' maar verwachtte '{verwachte_naam}'")
                        continue
                
                if naam in self._apparaten:
                    logger.debug(f"Reeds beheerd: {naam}")
                    continue
                
                apparaat = ESP32Device(mac, naam)
                self._voeg_apparaat_toe(apparaat)
                nieuwe_apparaten.append(apparaat)
                logger.info(f"Ontdekt: {naam} ({mac})")
        
        vertrouwde_gevonden = sum(1 for apparaat in self._apparaten.values() 
                          if apparaat.mac_adres.upper() in [m.upper() for m in self._vertrouwde_macs.keys()])
        
        if self._strikte_whitelist and vertrouwde_gevonden < totaal_apparaten_nodig:
            logger.warning(f"Scan gestopt, {vertrouwde_gevonden}/{totaal_apparaten_nodig} apparaten gevonden")
        else:
            logger.info(f"Scan voltooid, {len(nieuwe_apparaten)} nieuwe apparaat/apparaten gevonden")
        
        return nieuwe_apparaten


    async def verbind_alle(self) -> Dict[str, bool]:
        for naam, apparaat in self._apparaten.items():
            await apparaat.verbind()


    async def verbreek_alle(self) -> None:
        for apparaat in self._apparaten.values():
            await apparaat.verbreek()


    async def start_alle(self, correcte_kegel: str) -> Dict[str, bool]:
        for naam, apparaat in self._apparaten.items():
            if apparaat.verbonden:
                is_correcte = str(correcte_kegel).lower() in naam.lower()
                await apparaat.start_pollen(is_correcte)


    async def stop_alle(self) -> Dict[str, bool]:
        for naam, apparaat in self._apparaten.items():
            if apparaat.verbonden:
                await apparaat.stop_pollen()


    def zet_detectie_callback(self, callback: DetectieCallback) -> None:
        self._detectie_callback = callback
        for apparaat in self._apparaten.values():
            self._bind_detectie_aan_apparaat(apparaat)


    def verkrijg_alle_laatste_detecties(self) -> Dict[str, dict]:
        return self._laatste_detecties.copy()
    
    
    def verwijder_alle_laatste_detecties(self) -> None:
        self._laatste_detecties.clear()


    def zet_batterij_callback(self, callback: BatterijCallback) -> None:
        self._batterij_callback = callback

        for apparaat in self._apparaten.values():
            apparaat.bij_batterij = callback


    def zet_status_callback(self, callback: StatusCallback) -> None:
        self._status_callback = callback

        for apparaat in self._apparaten.values():
            apparaat.bij_status = callback


    def verkrijg_apparaat_gezondheid(self, timeout_seconden: float = 60.0) -> Dict[str, bool]:
        gezondheid: Dict[str, bool] = {}
        for naam, apparaat in self._apparaten.items():
            actief = apparaat.is_actief(timeout_seconden)
            gezondheid[naam] = actief
            
        return gezondheid


    def verkrijg_actieve_apparaten(self, timeout_seconden: float = 60.0) -> List[str]:
        actieve: List[str] = []
        for naam, apparaat in self._apparaten.items():
            if apparaat.is_actief(timeout_seconden):
                actieve.append(naam)

        return actieve


    def verkrijg_dode_apparaten(self, timeout_seconden: float = 60.0) -> List[str]:
        dode: List[str] = []
        for naam, apparaat in self._apparaten.items():
            if not apparaat.is_actief(timeout_seconden):
                dode.append(naam)

        return dode

    def log_gezondheid_status(self, timeout_seconden: float = 60.0) -> None:
        gezondheid = self.verkrijg_apparaat_gezondheid(timeout_seconden)
        actief = [naam for naam, status in gezondheid.items() if status]
        dood = [naam for naam, status in gezondheid.items() if not status]
        
        logger.info(f"Apparaat gezondheid: {len(actief)} actief, {len(dood)} dood")
        if actief:
            logger.info(f"  Actief: {', '.join(actief)}")

        if dood:
            logger.warning(f"  Dood/Niet-responsief: {', '.join(dood)}")
