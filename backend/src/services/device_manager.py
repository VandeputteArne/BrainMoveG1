import asyncio
import logging
import os
from bleak import BleakScanner
from dotenv import load_dotenv
from backend.src.services.cone import (
    Cone,
    DetectieCallback,
    BatterijCallback,
    APPARAAT_PREFIX
)

# Logging------------------------------------------------------------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# DeviceManager class------------------------------------------------
class DeviceManager:
    def __init__(self, sio=None) -> None:
        
        self._apparaten = {}
        self._sio = sio  # Socket.IO reference for emitting events
        
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
        
        self._detectie_callback = None
        self._batterij_callback = None

        self._laatste_detecties = {}
        
        # Scanning state
        self._scan_actief = False
        self._scan_taak = None
        self._apparaat_batterijen = {}  # Track battery percentages
    

    # Eigenschappen----------------------------------------------------------------------
    @property
    def apparaten(self):
        return self._apparaten.copy()
    

    @property
    def vertrouwde_macs(self):
        return self._vertrouwde_macs.copy()
    
    
    @property
    def strikte_whitelist(self) -> bool:
        return self._strikte_whitelist
    

    # Methoden--------------------------------------------------------------------------    
    def _bind_detectie_aan_apparaat(self, apparaat: Cone) -> None:
        def _wrapper(gebeurtenis: dict):
            self._laatste_detecties[apparaat.naam] = gebeurtenis
            if self._detectie_callback:
                self._detectie_callback(gebeurtenis)
        
        apparaat.bij_detectie = _wrapper


    def _voeg_apparaat_toe(self, apparaat: Cone) -> None:
        self._bind_detectie_aan_apparaat(apparaat)

        if self._batterij_callback:
            apparaat.bij_batterij = self._batterij_callback
        
        self._apparaten[apparaat.naam] = apparaat
        logger.info(f"Apparaat toegevoegd: {apparaat.naam}")


    async def scannen(self, max_pogingen: int = 10) -> list:
        nieuwe_apparaten = []
        vertrouwde_macs_upper = {m.upper() for m in self._vertrouwde_macs.keys()}
        
        for poging in range(max_pogingen):
            # Check if we already have all devices
            vertrouwde_gevonden = sum(1 for a in self._apparaten.values() if a.mac_adres.upper() in vertrouwde_macs_upper)
            if vertrouwde_gevonden >= len(self._vertrouwde_macs):
                break
            
            ontdekt = await BleakScanner.discover(timeout=self.scan_timeout)
            
            for ble_apparaat in ontdekt:
                if not ble_apparaat.name or not ble_apparaat.name.startswith(APPARAAT_PREFIX):
                    continue
                
                if ble_apparaat.name in self._apparaten:
                    continue
                
                # Whitelist check
                if self._strikte_whitelist and ble_apparaat.address.upper() not in vertrouwde_macs_upper:
                    continue
                
                apparaat = Cone(ble_apparaat.address, ble_apparaat.name)
                self._voeg_apparaat_toe(apparaat)
                nieuwe_apparaten.append(apparaat)
                logger.info(f"Ontdekt: {ble_apparaat.name} ({ble_apparaat.address})")
        
        return nieuwe_apparaten


    async def verbind_alle(self) -> dict:
        for naam, apparaat in self._apparaten.items():
            await apparaat.verbind()
        
        return {naam: apparaat.verbonden for naam, apparaat in self._apparaten.items()}


    async def verbreek_alle(self) -> None:
        for apparaat in self._apparaten.values():
            await apparaat.verbreek()


    async def start_alle(self, correcte_kegel: str) -> None:
        for apparaat in self._apparaten.values():
            if apparaat.verbonden:
                is_correcte = str(correcte_kegel).lower() in apparaat.naam.lower()
                await apparaat.start_pollen(is_correcte)


    async def stop_alle(self) -> None:
        for apparaat in self._apparaten.values():
            if apparaat.verbonden:
                await apparaat.stop_pollen()


    def zet_detectie_callback(self, callback: DetectieCallback) -> None:
        self._detectie_callback = callback
        for apparaat in self._apparaten.values():
            self._bind_detectie_aan_apparaat(apparaat)


    def verkrijg_alle_laatste_detecties(self) -> dict:
        return self._laatste_detecties.copy()
    
    
    def verwijder_alle_laatste_detecties(self) -> None:
        self._laatste_detecties.clear()


    def zet_batterij_callback(self, callback: BatterijCallback) -> None:
        self._batterij_callback = callback

        for apparaat in self._apparaten.values():
            apparaat.bij_batterij = callback


    # Device Scanning & Socket Integration-------------------------------------------
    def _neem_kleur_van_naam(self, naam: str) -> str:
        naam_lower = naam.lower()
        for kleur in ["blauw", "rood", "geel", "groen"]:
            if kleur in naam_lower:
                return kleur
        return "unknown"


    async def _emit_apparaat_status(self, apparaat: Cone, status: str, batterij: int = None) -> None:
        if not self._sio:
            return
        
        kleur = self._neem_kleur_van_naam(apparaat.naam)
        data = {
            "naam": apparaat.naam,
            "kleur": kleur,
            "mac": apparaat.mac_adres,
            "status": status
        }
        
        if batterij is not None:
            data["batterij"] = batterij
        
        event_naam = "device_connected" if status == "online" else "device_disconnected"
        await self._sio.emit(event_naam, data)
        logger.info(f"Socket emit: {event_naam} - {apparaat.naam}")


    def _setup_batterij_callback_voor_apparaat(self, apparaat: Cone)`` -> None:
        def _batterij_handler(gebeurtenis: dict):
            percentage = gebeurtenis.get("percentage", 0)
            self._apparaat_batterijen[apparaat.naam] = percentage
            asyncio.create_task(self._emit_apparaat_status(apparaat, "online", percentage))
            
            if self._batterij_callback:
                self._batterij_callback(gebeurtenis)
        
        apparaat.bij_batterij = _batterij_handler


    def _setup_verbreek_callback_voor_apparaat(self, apparaat: Cone) -> None:
        def _verbreek_handler():
            asyncio.create_task(self._emit_apparaat_status(apparaat, "offline"))
        
        apparaat.bij_verbreek = _verbreek_handler
    
    def _setup_herverbind_callback_voor_apparaat(self, apparaat: Cone) -> None:
        def _herverbind_handler():
            asyncio.create_task(self._emit_apparaat_status(apparaat, "online"))
        
        apparaat.bij_herverbind = _herverbind_handler


    async def start_apparaat_scan(self) -> None:
        if self._scan_actief:
            return
        
        self._scan_actief = True
        totaal_verwacht = len(self._vertrouwde_macs)
        vertrouwde_macs_upper = {m.upper() for m in self._vertrouwde_macs.keys()}
        
        try:
            while self._scan_actief:
                # Tel white listed aantal
                vertrouwde_verbonden = sum(
                    1 for a in self._apparaten.values() 
                    if a.verbonden and a.mac_adres.upper() in vertrouwde_macs_upper
                )
                
                # Verbonden of nie
                if vertrouwde_verbonden >= totaal_verwacht:
                    logger.info(f"Alle {totaal_verwacht} apparaten verbonden")
                    if self._sio:
                        await self._sio.emit('all_devices_connected', {
                            "aantal": totaal_verwacht,
                            "apparaten": [
                                {
                                    "naam": a.naam,
                                    "kleur": self._neem_kleur_van_naam(a.naam),
                                    "batterij": self._apparaat_batterijen.get(a.naam, 0)
                                }
                                for a in self._apparaten.values() if a.verbonden
                            ]
                        })
                    self._scan_actief = False
                    break
                
                # Emit progress
                if self._sio:
                    await self._sio.emit('scan_status', {
                        "gevonden": vertrouwde_verbonden,
                        "totaal": totaal_verwacht
                    })
                
                # Scan and connect new devices
                nieuwe_apparaten = await self.scannen(max_pogingen=1)
                
                for apparaat in nieuwe_apparaten:
                    if apparaat.mac_adres.upper() in vertrouwde_macs_upper:
                        self._setup_batterij_callback_voor_apparaat(apparaat)
                        self._setup_verbreek_callback_voor_apparaat(apparaat)
                        self._setup_herverbind_callback_voor_apparaat(apparaat)
                        success = await apparaat.verbind()
                        if success:
                            # Emit direct na verbinding, batterij update volgt via callback
                            await self._emit_apparaat_status(apparaat, "online")
                        else:
                            logger.warning(f"Verbinding mislukt voor {apparaat.naam}, opnieuw proberen")
                
                await asyncio.sleep(2.0)
                
        except asyncio.CancelledError:
            logger.info("Apparaat scan geannuleerd")
            self._scan_actief = False
            raise
        finally:
            logger.info(f"Apparaat scan gestopt - {vertrouwde_verbonden}/{totaal_verwacht} verbonden")


    async def stop_apparaat_scan(self) -> None:
        if self._scan_actief:
            logger.info("Stoppen apparaat scan")
            self._scan_actief = False
            
            if self._scan_taak:
                self._scan_taak.cancel()
                try:
                    await self._scan_taak
                except asyncio.CancelledError:
                    pass
                self._scan_taak = None


    def verkrijg_apparaten_status(self) -> list:
        status_lijst = []
        
        for mac, naam in self._vertrouwde_macs.items():
            apparaat = self._apparaten.get(naam)
            is_online = apparaat and apparaat.verbonden
            
            status_lijst.append({
                "naam": naam,
                "kleur": self._neem_kleur_van_naam(naam),
                "mac": mac,
                "status": "online" if is_online else "offline",
                "batterij": self._apparaat_batterijen.get(naam) if is_online else None
            })
        
        return status_lijst