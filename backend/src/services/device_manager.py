import asyncio
import logging
import os
from datetime import datetime, timezone
from bleak import BleakScanner
from dotenv import load_dotenv
from backend.src.services.cone import Cone, DetectieCallback, BatterijCallback, APPARAAT_PREFIX
from backend.src.services.ble_thread import start_ble_thread

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class DeviceManager:
    """
    Manages BLE devices with operations running on a separate thread.

    All BLE operations (scan, connect, write) run on a dedicated BLE thread,
    keeping the main event loop free for Socket.io communications.
    """

    def __init__(self, sio=None) -> None:
        self._apparaten = {}
        self._sio = sio
        self._main_loop = None  # Reference to main event loop for socket emissions
        load_dotenv()

        # Start the BLE thread
        self._ble_thread = start_ble_thread()

        # Lock must be created on the BLE thread
        self.connect_lock = None
        self._init_lock_future = self._ble_thread.run_nowait(self._create_lock())

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

    async def _create_lock(self):
        """Create the lock on the BLE thread."""
        self.connect_lock = asyncio.Lock()

    def _store_main_loop(self):
        """Store reference to main event loop for cross-thread socket emissions."""
        try:
            self._main_loop = asyncio.get_running_loop()
        except RuntimeError:
            self._main_loop = None

    def _emit_from_ble_thread(self, event: str, data: dict):
        """Safely emit socket event from BLE thread to main loop."""
        if not self._sio or not self._main_loop:
            return

        async def _do_emit():
            await self._sio.emit(event, data)

        # Schedule the emit on the main event loop
        self._main_loop.call_soon_threadsafe(
            lambda: asyncio.create_task(_do_emit())
        )

    @property
    def apparaten(self):
        return self._apparaten.copy()

    @property
    def vertrouwde_macs(self):
        return self._vertrouwde_macs.copy()

    # ==================== BLE Operations (run on BLE thread) ====================

    async def _ble_keepalive_loop(self, interval: float = 600.0, battery_timeout: float = 5.0):
        """Keepalive loop - runs on BLE thread."""
        logger.info("Keepalive gestart (BLE thread)")
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

                # Emit from BLE thread to main loop
                self._emit_from_ble_thread("keepalive", {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "apparaten": keepalive_status
                })

                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            logger.info("Keepalive gestopt")

    async def _ble_scannen(self, max_pogingen: int = 10) -> list:
        """Scan for BLE devices - runs on BLE thread."""
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

    async def _ble_verbind_alle(self) -> dict:
        """Connect all devices - runs on BLE thread."""
        for app in self._apparaten.values():
            if not app.verbonden:
                await app.verbind()
                await asyncio.sleep(2.0)
        return {n: a.verbonden for n, a in self._apparaten.items()}

    async def _ble_verbreek_alle(self) -> None:
        """Disconnect all devices - runs on BLE thread."""
        for app in self._apparaten.values():
            await app.verbreek()

    async def _ble_start_alle(self) -> None:
        """Start polling all devices - runs on BLE thread."""
        for app in self._apparaten.values():
            if app.verbonden:
                await app.start_pollen()

    async def _ble_set_correct_kegel(self, correcte_kegel: str) -> None:
        """Set correct cone - runs on BLE thread."""
        for app in self._apparaten.values():
            if app.verbonden and str(correcte_kegel).lower() in app.naam.lower():
                await app.set_correct(True)

    async def _ble_reset_correct_kegel(self, kegel: str) -> None:
        """Reset correct cone - runs on BLE thread."""
        for app in self._apparaten.values():
            if app.verbonden and str(kegel).lower() in app.naam.lower():
                await app.set_correct(False)

    async def _ble_stop_alle(self) -> None:
        """Stop polling all devices - runs on BLE thread."""
        for app in self._apparaten.values():
            if app.verbonden:
                await app.stop_pollen()

    async def _ble_apparaat_scan_loop(self) -> None:
        """Continuous scan loop - runs on BLE thread."""
        macs_upper = {m.upper() for m in self._vertrouwde_macs.keys()}

        try:
            while self._scan_actief:
                aantal_verbonden = sum(1 for a in self._apparaten.values() if a.verbonden and a.mac_adres.upper() in macs_upper)

                if aantal_verbonden >= len(self._vertrouwde_macs):
                    logger.info("Alles verbonden")
                    self._scan_actief = False
                    break

                for app in await self._ble_scannen(1):
                    if app.mac_adres.upper() in macs_upper:
                        self._setup_callbacks(app)
                        if await app.verbind():
                            self._emit_device_status(app, "online")

                await asyncio.sleep(3.0)
        except asyncio.CancelledError:
            self._scan_actief = False
            raise

    # ==================== Public API (called from main thread) ====================

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

    def _emit_device_status(self, app: Cone, status: str, batterij: int = None):
        """Emit device status - safe to call from any thread."""
        kleur = "unknown"
        for k in ["blauw", "rood", "geel", "groen"]:
            if k in app.naam.lower():
                kleur = k
                break

        event = "device_connected" if status == "online" else "device_disconnected"
        data = {"kleur": kleur, "status": status, "batterij": batterij}

        self._emit_from_ble_thread(event, data)

    def _setup_callbacks(self, app: Cone) -> None:
        def _batt(gebeurtenis):
            percentage = gebeurtenis.get("percentage", 0)
            self._apparaat_batterijen[app.naam] = percentage
            self._emit_device_status(app, "online", percentage)
            if self._batterij_callback:
                self._batterij_callback(gebeurtenis)
        app.bij_batterij = _batt

        def _verbreek():
            self._emit_device_status(app, "offline")
        app.bij_verbreek = _verbreek

        def _herverbind():
            self._emit_device_status(app, "online")
        app.bij_herverbind = _herverbind

    # ==================== Async wrappers (bridge main thread to BLE thread) ====================

    async def scannen(self, max_pogingen: int = 10) -> list:
        """Scan for devices - runs on BLE thread, awaitable from main thread."""
        return await self._ble_thread.run(self._ble_scannen(max_pogingen))

    async def verbind_alle(self) -> dict:
        """Connect all devices - runs on BLE thread."""
        return await self._ble_thread.run(self._ble_verbind_alle())

    async def verbreek_alle(self) -> None:
        """Disconnect all devices - runs on BLE thread."""
        await self.stop_apparaat_scan()
        await self._ble_thread.run(self._ble_verbreek_alle())

    async def start_alle(self) -> None:
        """Start polling - runs on BLE thread."""
        await self._ble_thread.run(self._ble_start_alle())

    async def set_correct_kegel(self, correcte_kegel: str) -> None:
        """Set correct cone - fire and forget on BLE thread (non-blocking)."""
        self._ble_thread.run_nowait(self._ble_set_correct_kegel(correcte_kegel))

    async def reset_correct_kegel(self, kegel: str) -> None:
        """Reset correct cone - fire and forget on BLE thread (non-blocking)."""
        self._ble_thread.run_nowait(self._ble_reset_correct_kegel(kegel))

    async def stop_alle(self) -> None:
        """Stop polling - runs on BLE thread."""
        await self._ble_thread.run(self._ble_stop_alle())

    def zet_detectie_callback(self, cb: DetectieCallback) -> None:
        self._detectie_callback = cb
        for app in self._apparaten.values():
            self._bind_detectie_aan_apparaat(app)

    def zet_batterij_callback(self, cb: BatterijCallback) -> None:
        self._batterij_callback = cb

    def verkrijg_alle_laatste_detecties(self) -> dict:
        return self._laatste_detecties.copy()

    def verwijder_alle_laatste_detecties(self) -> None:
        self._laatste_detecties.clear()

    async def _emit_status(self, app: Cone, status: str, batterij: int = None) -> None:
        """Emit status on main loop - for compatibility."""
        if not self._sio: return

        kleur = "unknown"
        for k in ["blauw", "rood", "geel", "groen"]:
            if k in app.naam.lower():
                kleur = k
                break

        event = "device_connected" if status == "online" else "device_disconnected"
        data = {"kleur": kleur, "status": status, "batterij": batterij}

        await self._sio.emit(event, data)

    async def start_apparaat_scan(self) -> None:
        """Start scanning for devices - scan runs on BLE thread."""
        if self._scan_actief:
            return

        # Store main loop reference for cross-thread emissions
        self._store_main_loop()

        self._scan_actief = True

        # Start keepalive on BLE thread
        self._ble_thread.run_nowait(self._ble_keepalive_loop())

        # Start scan loop on BLE thread
        self._ble_thread.run_nowait(self._ble_apparaat_scan_loop())

        logger.info("Apparaat scan gestart op BLE thread")

    async def stop_apparaat_scan(self) -> None:
        self._scan_actief = False
        # Note: BLE thread tasks will check _scan_actief and stop themselves
        logger.info("Apparaat scan gestopt")

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
