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

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class DeviceManager:
    def __init__(self, sio=None) -> None:
        self._apparaten = {}
        self._sio = sio
        
        self.connect_lock = asyncio.Lock()
        
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
        self._apparaat_batterijen = {}

        self._scan_actief = False
        self._scan_taak = None
        self._keepalive_taak = None

    # Eigenschappen
    @property
    def apparaten(self):
        return self._apparaten.copy()

    @property
    def vertrouwde_macs(self):
        return self._vertrouwde_macs.copy()

    @property
    def strikte_whitelist(self) -> bool:
        return self._strikte_whitelist

    async def keepalive_loop(self, interval: float = 600.0, battery_timeout: float = 5.0):
        logger.info(f"Keepalive loop gestart (interval: {interval}s)")
        try:
            while True:
                for apparaat in list(self._apparaten.values()):
                    if not apparaat.verbonden or apparaat.is_aan_het_pollen:
                        continue

                    batterij_event = asyncio.Event()
                    
                    orig_callback = apparaat.bij_batterij

                    def _tijdelijke_batterij_wrapper(gebeurtenis):
                        batterij_event.set()
                        
                        percentage = gebeurtenis.get("percentage", 0)
                        self._apparaat_batterijen[apparaat.naam] = percentage
                        
                        if orig_callback:
                            orig_callback(gebeurtenis)

                    apparaat.bij_batterij = _tijdelijke_batterij_wrapper

                    try:
                        logger.debug(f"Verstuur keepalive naar {apparaat.naam}")
                        if await apparaat.send_keepalive():
                            try:
                                await asyncio.wait_for(batterij_event.wait(), timeout=battery_timeout)
                                logger.debug(f"Keepalive bevestigd voor {apparaat.naam}")
                            except asyncio.TimeoutError:
                                logger.warning(f"Geen batterij response van {apparaat.naam} na keepalive (timeout)")
                        else:
                            logger.warning(f"Kon keepalive commando niet versturen naar {apparaat.naam}")
                            
                    except Exception as e:
                        logger.error(f"Fout tijdens keepalive voor {apparaat.naam}: {e}")
                    finally:
                        apparaat.bij_batterij = orig_callback

                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            logger.info("Keepalive loop gestopt")

    # Methoden
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
            vertrouwde_gevonden = sum(1 for a in self._apparaten.values() if a.mac_adres.upper() in vertrouwde_macs_upper)
            if vertrouwde_gevonden >= len(self._vertrouwde_macs):
                break
            
            ontdekt = await BleakScanner.discover(timeout=self.scan_timeout)
            
            for ble_apparaat in ontdekt:
                if not ble_apparaat.name or not ble_apparaat.name.startswith(APPARAAT_PREFIX):
                    continue
                
                if ble_apparaat.name in self._apparaten:
                    continue
                
                if self._strikte_whitelist and ble_apparaat.address.upper() not in vertrouwde_macs_upper:
                    continue
                
                apparaat = Cone(ble_apparaat.address, ble_apparaat.name, lock=self.connect_lock)
                
                self._voeg_apparaat_toe(apparaat)
                nieuwe_apparaten.append(apparaat)
                logger.info(f"Ontdekt: {ble_apparaat.name} ({ble_apparaat.address})")
        
        return nieuwe_apparaten

    async def verbind_alle(self) -> dict:
        logger.info("Starten met verbinden van alle apparaten...")
        
        for naam, apparaat in self._apparaten.items():
            if not apparaat.verbonden:
                logger.info(f"Verbinden met {naam}...")
                await apparaat.verbind()
                await asyncio.sleep(2.0)
        
        return {naam: apparaat.verbonden for naam, apparaat in self._apparaten.items()}

    async def verbreek_alle(self) -> None:
        await self.stop_apparaat_scan()
        
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
            "kleur": kleur,
            "status": status,
            "batterij": batterij
        }

        event_naam = "device_connected" if status == "online" else "device_disconnected"
        await self._sio.emit(event_naam, data)
        logger.info(f"Socket emit: {event_naam} - {apparaat.naam}")

    def _setup_batterij_callback_voor_apparaat(self, apparaat: Cone) -> None:
        def _batterij_handler(gebeurtenis: dict):
            percentage = gebeurtenis.get("percentage", 0)
            self._apparaat_batterijen[apparaat.naam] = percentage
            
            # Emit status naar frontend
            asyncio.create_task(self._emit_apparaat_status(apparaat, "online", percentage))
            
            # Roep externe callback aan indien ingesteld
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
        
        # Start de keepalive taak als die nog niet draait
        if self._keepalive_taak is None or self._keepalive_taak.done():
            self._keepalive_taak = asyncio.create_task(self.keepalive_loop())

        totaal_verwacht = len(self._vertrouwde_macs)
        vertrouwde_macs_upper = {m.upper() for m in self._vertrouwde_macs.keys()}
        
        try:
            while self._scan_actief:
                vertrouwde_verbonden = sum(
                    1 for a in self._apparaten.values() 
                    if a.verbonden and a.mac_adres.upper() in vertrouwde_macs_upper
                )
                
                if vertrouwde_verbonden >= totaal_verwacht:
                    logger.info(f"Alle {totaal_verwacht} apparaten verbonden")
                    self._scan_actief = False 
                    break
                
                nieuwe_apparaten = await self.scannen(max_pogingen=1)
                
                for apparaat in nieuwe_apparaten:
                    if apparaat.mac_adres.upper() in vertrouwde_macs_upper:
                        self._setup_batterij_callback_voor_apparaat(apparaat)
                        self._setup_verbreek_callback_voor_apparaat(apparaat)
                        self._setup_herverbind_callback_voor_apparaat(apparaat)
                        
                        success = await apparaat.verbind()
                        if success:
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
        
        if self._keepalive_taak:
            logger.info("Stoppen keepalive taak")
            self._keepalive_taak.cancel()
            try:
                await self._keepalive_taak
            except asyncio.CancelledError:
                pass
            self._keepalive_taak = None

    def verkrijg_apparaten_status(self) -> list:
        status_lijst = []
        
        for mac, naam in self._vertrouwde_macs.items():
            apparaat = self._apparaten.get(naam)
            is_online = apparaat and apparaat.verbonden
            
            status_lijst.append({
                "kleur": self._neem_kleur_van_naam(naam),
                "status": "online" if is_online else "offline",
                "batterij": self._apparaat_batterijen.get(naam) if is_online else None
            })
        
        return status_lijst