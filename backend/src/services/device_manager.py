import asyncio
import logging
import os
from bleak import BleakScanner
from dotenv import load_dotenv
from backend.src.services.cone import Cone, DetectieCallback, BatterijCallback, APPARAAT_PREFIX

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class DeviceManager:
    def __init__(self, sio=None) -> None:
        self._apparaten = {}
        self._sio = sio
        self.connect_lock = asyncio.Lock()
        load_dotenv()
        
        self.veiligheids_byte = int(os.getenv("VEILIGHEIDS_BYTE", "0x42"), 0)
        self.scan_timeout = float(os.getenv("SCAN_TIMEOUT", "5.0"))
        self._strikte_whitelist = os.getenv("STRIKTE_WHITELIST", "").lower() == "true"
        
        self._vertrouwde_macs = {}
        for k in ("BLAUW", "ROOD", "GEEL", "GROEN"):
            mac = os.getenv(f"APPARAAT_BM_{k}")
            if mac: 
                self._vertrouwde_macs[mac] = f"BM-{k.capitalize()}"
        
        self._detectie_callback = None
        self._batterij_callback = None
        self._laatste_detecties = {}
        self._apparaat_batterijen = {}
        self._scan_actief = False
        self._scan_taak = None
        self._keepalive_taak = None

    @property
    def apparaten(self): return self._apparaten.copy()
    
    @property
    def vertrouwde_macs(self): return self._vertrouwde_macs.copy()

    async def keepalive_loop(self, interval: float = 600.0, battery_timeout: float = 5.0):
        logger.info("Keepalive gestart")
        import datetime
        try:
            while True:
                keepalive_status = []
                for apparaat in list(self._apparaten.values()):
                    if not apparaat.verbonden or apparaat.is_aan_het_pollen:
                        continue

                    evt = asyncio.Event()
                    originele_callback = apparaat.bij_batterij

                    def _tijdelijke_wrapper(gebeurtenis):
                        evt.set()
                        percentage = gebeurtenis.get("percentage", 0)
                        self._apparaat_batterijen[apparaat.naam] = percentage
                        if originele_callback:
                            originele_callback(gebeurtenis)

                    apparaat.bij_batterij = _tijdelijke_wrapper

                    try:
                        result = await apparaat.send_keepalive()
                        if result:
                            try:
                                await asyncio.wait_for(evt.wait(), timeout=battery_timeout)
                                status = "ok"
                            except asyncio.TimeoutError:
                                logger.warning(f"Keepalive timeout {apparaat.naam}")
                                status = "timeout"
                        else:
                            status = "failed"
                    except Exception as e:
                        logger.error(f"Keepalive fout {apparaat.naam}: {e}")
                        status = "error"
                    finally:
                        apparaat.bij_batterij = originele_callback

                    keepalive_status.append({
                        "apparaat": apparaat.naam,
                        "status": status,
                        "batterij": self._apparaat_batterijen.get(apparaat.naam)
                    })

                if self._sio:
                    await self._sio.emit("keepalive", {
                        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                        "apparaten": keepalive_status
                    })

                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            logger.info("Keepalive gestopt")

    def _bind_detectie_aan_apparaat(self, app: Cone) -> None:
        def _wrapper(gebeurtenis):
            self._laatste_detecties[app.naam] = gebeurtenis
            if self._detectie_callback: 
                self._detectie_callback(gebeurtenis)
        app.bij_detectie = _wrapper

    def _voeg_apparaat_toe(self, app: Cone) -> None:
        self._bind_detectie_aan_apparaat(app)
        if self._batterij_callback: 
            app.bij_batterij = self._batterij_callback
            
        self._apparaten[app.naam] = app
        logger.info(f"Toegevoegd: {app.naam}")

    async def scannen(self, max_pogingen: int = 10) -> list:
        nieuwe = []
        macs_upper = {m.upper() for m in self._vertrouwde_macs.keys()}
        
        for _ in range(max_pogingen):
            huidig_aantal = sum(1 for a in self._apparaten.values() if a.mac_adres.upper() in macs_upper)
            if huidig_aantal >= len(self._vertrouwde_macs): 
                break
                
            ontdekt = await BleakScanner.discover(timeout=self.scan_timeout)
            
            for d in ontdekt:
                if not d.name or not d.name.startswith(APPARAAT_PREFIX): continue
                if d.name in self._apparaten: continue
                if self._strikte_whitelist and d.address.upper() not in macs_upper: continue
                
                app = Cone(d.address, d.name, lock=self.connect_lock)
                self._voeg_apparaat_toe(app)
                nieuwe.append(app)
        return nieuwe

    async def verbind_alle(self) -> dict:
        for app in self._apparaten.values():
            if not app.verbonden:
                await app.verbind()
                await asyncio.sleep(2.0)
        return {n: a.verbonden for n, a in self._apparaten.items()}

    async def verbreek_alle(self) -> None:
        await self.stop_apparaat_scan()
        for app in self._apparaten.values(): 
            await app.verbreek()

    async def start_alle(self) -> None:
        for app in self._apparaten.values():
            if app.verbonden:
                await app.start_pollen()

    async def set_correct_kegel(self, correcte_kegel: str) -> None:
        for app in self._apparaten.values():
            if app.verbonden and str(correcte_kegel).lower() in app.naam.lower():
                await app.set_correct(True)

    async def reset_correct_kegel(self, kegel: str) -> None:
        for app in self._apparaten.values():
            if app.verbonden and str(kegel).lower() in app.naam.lower():
                await app.set_correct(False)

    async def stop_alle(self) -> None:
        for app in self._apparaten.values():
            if app.verbonden: 
                await app.stop_pollen()

    def zet_detectie_callback(self, cb: DetectieCallback) -> None:
        self._detectie_callback = cb
        for app in self._apparaten.values(): 
            self._bind_detectie_aan_apparaat(app)

    def zet_batterij_callback(self, cb: BatterijCallback) -> None:
        self._batterij_callback = cb
        
    def verkrijg_alle_laatste_detecties(self) -> dict: return self._laatste_detecties.copy()
    def verwijder_alle_laatste_detecties(self) -> None: self._laatste_detecties.clear()

    async def _emit_status(self, app: Cone, status: str, batterij: int = None) -> None:
        if not self._sio: return
        
        kleur = "unknown"
        for k in ["blauw", "rood", "geel", "groen"]:
            if k in app.naam.lower(): 
                kleur = k
                break
                
        event = "device_connected" if status == "online" else "device_disconnected"
        data = {"kleur": kleur, "status": status, "batterij": batterij}
        
        await self._sio.emit(event, data)

    def _setup_callbacks(self, app: Cone) -> None:
        def _batt(gebeurtenis):
            percentage = gebeurtenis.get("percentage", 0)
            self._apparaat_batterijen[app.naam] = percentage
            asyncio.create_task(self._emit_status(app, "online", percentage))
            if self._batterij_callback: 
                self._batterij_callback(gebeurtenis)
        app.bij_batterij = _batt
        
        def _verbreek():
            asyncio.create_task(self._emit_status(app, "offline"))
        app.bij_verbreek = _verbreek
        
        def _herverbind():
            asyncio.create_task(self._emit_status(app, "online"))
        app.bij_herverbind = _herverbind

    async def start_apparaat_scan(self) -> None:
        if self._scan_actief: return
        self._scan_actief = True
        
        if not self._keepalive_taak or self._keepalive_taak.done():
            self._keepalive_taak = asyncio.create_task(self.keepalive_loop())

        macs_upper = {m.upper() for m in self._vertrouwde_macs.keys()}
        
        try:
            while self._scan_actief:
                aantal_verbonden = sum(1 for a in self._apparaten.values() if a.verbonden and a.mac_adres.upper() in macs_upper)
                
                if aantal_verbonden >= len(self._vertrouwde_macs):
                    logger.info("Alles verbonden")
                    self._scan_actief = False
                    break
                
                for app in await self.scannen(1):
                    if app.mac_adres.upper() in macs_upper:
                        self._setup_callbacks(app)
                        if await app.verbind(): 
                            await self._emit_status(app, "online")
                            
                await asyncio.sleep(2.0)
        except asyncio.CancelledError: 
            self._scan_actief = False
            raise

    async def stop_apparaat_scan(self) -> None:
        self._scan_actief = False
        if self._scan_taak: self._scan_taak.cancel()
        if self._keepalive_taak: self._keepalive_taak.cancel()
        self._scan_taak = None
        self._keepalive_taak = None

    def verkrijg_apparaten_status(self) -> list:
        status_lijst = []
        for mac, naam in self._vertrouwde_macs.items():
            app = self._apparaten.get(naam)
            is_verbonden = app and app.verbonden
            
            kleur = "unknown"
            for k in ["blauw","rood","geel","groen"]:
                if k in naam.lower():
                    kleur = k
                    break

            status_lijst.append({
                "kleur": kleur,
                "status": "online" if is_verbonden else "offline",
                "batterij": self._apparaat_batterijen.get(naam) if is_verbonden else None
            })
        return status_lijst