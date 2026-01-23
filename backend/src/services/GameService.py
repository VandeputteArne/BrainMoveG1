import asyncio
import random
import time
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class GameService:
    def __init__(self, device_manager, sio, hardware_delay: float = 0.07):
        self.device_manager = device_manager
        self.sio = sio
        self.hardware_delay = hardware_delay
        self.stop_event = asyncio.Event()
    
    async def run_colorgame(self, aantal_rondes: int, kleuren: List[str], snelheid: float) -> List[Dict]:
        """Voert het colorgame uit en returnt de rondes"""
        colorgame_rondes = []
        max_tijd = float(snelheid)
        
        detectie_event = asyncio.Event()
        detected_color = {}
        
        def on_detectie(gebeurtenis):
            detected_color.clear()
            detected_color.update(gebeurtenis)
            detectie_event.set()
        
        self.device_manager.zet_detectie_callback(on_detectie)
        await self.device_manager.start_alle()
        
        for ronde in range(1, aantal_rondes + 1):
            if self.stop_event.is_set():
                logger.info("Game gestopt door gebruiker")
                break
            
            gekozen_kleur = random.choice(kleuren).upper()
            
            await self.sio.emit('gekozen_kleur', {
                'rondenummer': ronde,
                'maxronden': aantal_rondes,
                'kleur': gekozen_kleur
            })
            logger.info(f"Round {ronde}: Chosen color = {gekozen_kleur}")
            
            await asyncio.sleep(0.2)
            await self.device_manager.set_correct_kegel(gekozen_kleur)
            
            detectie_event.clear()
            detected_color.clear()
            starttijd = time.time()
            
            try:
                detectie_task = asyncio.create_task(detectie_event.wait())
                stop_task = asyncio.create_task(self.stop_event.wait())
                
                done, pending = await asyncio.wait(
                    [detectie_task, stop_task],
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                for task in pending:
                    task.cancel()
                
                if stop_task in done:
                    logger.info("Game gestopt tijdens wachten op detectie")
                    break
                
                if detectie_task in done:
                    reactietijd = round(time.time() - starttijd, 2) - self.hardware_delay
                    detected_kleur = detected_color.get("kleur", "").lower()
                    
                    if (max_tijd - reactietijd) < 0:
                        reactietijd = max_tijd
                        status = "te laat"
                        logger.info(f"Too late! Reaction time: {reactietijd}s")
                    elif detected_kleur == gekozen_kleur.lower():
                        status = "correct"
                        logger.info(f"Correct! Reaction time: {reactietijd}s")
                    else:
                        status = "fout"
                        reactietijd += max_tijd
                        logger.info(f"Wrong color! Detected: {detected_kleur}, Expected: {gekozen_kleur}")
                else:
                    reactietijd = max_tijd
                    status = "te laat"
                    logger.info(f"Too late! Timeout after {max_tijd}s")
                    
            except Exception as e:
                logger.error(f"Error in colorgame ronde: {e}")
                reactietijd = max_tijd
                status = "fout"
            
            colorgame_rondes.append({
                "rondenummer": ronde,
                "waarde": reactietijd,
                "uitkomst": status,
            })
            
            await self.device_manager.reset_correct_kegel(gekozen_kleur)
        
        await self.device_manager.stop_alle()
        self.device_manager.zet_detectie_callback(None)
        await self.sio.emit('game_einde', {"status": "game gedaan"})
        
        return colorgame_rondes
    
    async def run_memorygame(self, snelheid: float, aantal_rondes: int, kleuren: List[str]) -> List[Dict]:
        """Voert het memorygame uit en returnt de rondes"""
        geheugen_lijst = []
        rondes_memory = []

        detectie_event = asyncio.Event()
        detected_color = {}

        def on_detectie(gebeurtenis):
            detected_color.clear()
            detected_color.update(gebeurtenis)
            detectie_event.set()

        self.device_manager.zet_detectie_callback(on_detectie)

        for ronde in range(1, aantal_rondes + 1):
            if self.stop_event.is_set():
                logger.info("Game gestopt door gebruiker")
                break
                
            nieuwe_kleur = random.choice(kleuren)
            geheugen_lijst.append(nieuwe_kleur)
            await self.sio.emit('ronde_start', {'rondenummer': ronde, 'maxronden': aantal_rondes})

            await asyncio.sleep(3)
            await self.sio.emit('wacht_even', {'bericht': 'start'})

            for kleur in geheugen_lijst:
                await self.sio.emit('toon_kleur', {'kleur': kleur.upper()})
                logger.debug(f"Toon kleur: {kleur}")
                await asyncio.sleep(snelheid)

            await self.sio.emit('kleuren_getoond', {'aantal': len(geheugen_lijst)})
            await self.device_manager.start_alle()

            starttijd = time.time()
            status = "correct"

            for verwachte_kleur in geheugen_lijst:
                if self.stop_event.is_set():
                    logger.info("Game gestopt tijdens memory sequence")
                    status = "gestopt"
                    break
                
                detectie_event.clear()
                detected_color.clear()

                await self.device_manager.set_correct_kegel(verwachte_kleur)

                try:
                    detectie_task = asyncio.create_task(detectie_event.wait())
                    stop_task = asyncio.create_task(self.stop_event.wait())
                    
                    done, pending = await asyncio.wait(
                        [detectie_task, stop_task],
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    # Properly cancel and await pending tasks
                    for task in pending:
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            pass
                    
                    await self.device_manager.reset_correct_kegel(verwachte_kleur)
                    
                    if stop_task in done:
                        logger.info("Game gestopt tijdens wachten op aanraking")
                        status = "gestopt"
                        break
                    
                    if detectie_task in done:
                        detected_kleur = detected_color.get("kleur", "").lower()
                        
                        if detected_kleur != verwachte_kleur.lower():
                            await self.sio.emit('fout_kleur', {'status': 'game over'})
                            status = "fout"
                            logger.info(f"Fout! Verwacht: {verwachte_kleur}, Gekregen: {detected_kleur}")
                            break
                        
                        logger.debug(f"Correct: {detected_kleur}")
                    else:
                        await self.sio.emit('fout_kleur', {'status': 'timeout'})
                        status = "fout"
                        logger.info("Timeout: Te lang gewacht op aanraking")
                        break

                except Exception as e:
                    await self.device_manager.reset_correct_kegel(verwachte_kleur)
                    logger.error(f"Error in memory sequence: {e}")
                    status = "fout"
                    break

            eindtijd = time.time()
            reactietijd = round(eindtijd - starttijd, 2)
            await self.sio.emit('ronde_einde', {'ronde': ronde, 'status': status})
            logger.info(f"Ronde {ronde} klaar: {status}")
            await self.device_manager.stop_alle()

            rondes_memory.append({
                'rondenummer': ronde,
                'reactietijd': reactietijd,
                'status': status
            })

            if status == "fout":
                break

        self.device_manager.zet_detectie_callback(None)
        await self.sio.emit('game_einde', {"status": "game gedaan"})
        logger.info("Einde memory game")
        return rondes_memory
    
    async def run_numbergame(self, aantal_rondes: int, kleuren: List[str], snelheid: float) -> List[Dict]:
        """Voert het numbergame uit en returnt de rondes"""
        numbergame_rondes = []
        max_tijd = float(snelheid)
        
        # Shuffle de gekozen kleuren en maak een random mapping
        beschikbare_kleuren = kleuren.copy()
        random.shuffle(beschikbare_kleuren)
        
        # Maak mapping van kleuren naar nummers (1, 2, 3, ...)
        kleur_naar_nummer = {}
        for index, kleur in enumerate(beschikbare_kleuren):
            kleur_naar_nummer[kleur] = index + 1
        
        max_nummer = len(beschikbare_kleuren)
        
        detectie_event = asyncio.Event()
        detected_color = {}
        
        def on_detectie(gebeurtenis):
            detected_color.clear()
            detected_color.update(gebeurtenis)
            detectie_event.set()
        
        self.device_manager.zet_detectie_callback(on_detectie)
        
        # Stuur de random mapping naar de frontend
        await self.sio.emit('nummer_mapping', {
            'mapping': kleur_naar_nummer
        })
        logger.info(f"Random mapping: {kleur_naar_nummer}")
        
        # Wacht even zodat de gebruiker de mapping kan zien
        await asyncio.sleep(5)
        
        
        # Start de sensors NA de mapping display
        await self.device_manager.start_alle()
        
        
        for ronde in range(1, aantal_rondes + 1):
            if self.stop_event.is_set():
                logger.info("Game gestopt door gebruiker")
                break
            
            # Kies een random nummer tussen 1 en het aantal gekozen kleuren
            gekozen_nummer = random.randint(1, max_nummer)
            
            # Vind de bijbehorende kleur
            verwachte_kleur = None
            for kleur, nummer in kleur_naar_nummer.items():
                if nummer == gekozen_nummer:
                    verwachte_kleur = kleur
                    break
            
            await self.sio.emit('gekozen_nummer', {
                'rondenummer': ronde,
                'maxronden': aantal_rondes,
                'nummer': gekozen_nummer
            })
            logger.info(f"Round {ronde}: Chosen number = {gekozen_nummer}, Expected color = {verwachte_kleur}")
            
            await asyncio.sleep(0.2)
            await self.device_manager.set_correct_kegel(verwachte_kleur)
            
            detectie_event.clear()
            detected_color.clear()
            starttijd = time.time()
            
            try:
                detectie_task = asyncio.create_task(detectie_event.wait())
                stop_task = asyncio.create_task(self.stop_event.wait())
                
                done, pending = await asyncio.wait(
                    [detectie_task, stop_task],
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # Properly cancel and await pending tasks
                for task in pending:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                
                if stop_task in done:
                    logger.info("Game gestopt tijdens wachten op detectie")
                    break
                
                if detectie_task in done:
                    reactietijd = round(time.time() - starttijd, 2) - self.hardware_delay
                    detected_kleur = detected_color.get("kleur", "").lower()
                    
                    if (max_tijd - reactietijd) < 0:
                        reactietijd = max_tijd
                        status = "te laat"
                        logger.info(f"Too late! Reaction time: {reactietijd}s")
                    elif detected_kleur == verwachte_kleur.lower():
                        status = "correct"
                        logger.info(f"Correct! Reaction time: {reactietijd}s")
                    else:
                        status = "fout"
                        reactietijd += max_tijd
                        logger.info(f"Wrong color! Detected: {detected_kleur}, Expected: {verwachte_kleur}")
                else:
                    reactietijd = max_tijd
                    status = "te laat"
                    logger.info(f"Too late! Timeout after {max_tijd}s")
                    
            except Exception as e:
                logger.error(f"Error in numbergame ronde: {e}")
                reactietijd = max_tijd
                status = "fout"
            
            numbergame_rondes.append({
                "rondenummer": ronde,
                "waarde": reactietijd,
                "uitkomst": status,
            })
            
            await self.device_manager.reset_correct_kegel(verwachte_kleur)
        
        await self.device_manager.stop_alle()
        self.device_manager.zet_detectie_callback(None)
        await self.sio.emit('game_einde', {"status": "game gedaan"})
        
        return numbergame_rondes
    
    async def run_fallingcolorgame(self, aantal_rondes: int, kleuren: List[str], snelheid: float) -> List[Dict]:
        """Voert het falling color game uit waarbij kleuren van 100% naar 0% vallen"""
        fallingcolor_rondes = []
        val_tijd = float(snelheid)  # Tijd om van 100% naar 0% te vallen
        update_interval = 0.05  # Update percentage elke 50ms
        
        detectie_event = asyncio.Event()
        detected_color = {}
        
        def on_detectie(gebeurtenis):
            detected_color.clear()
            detected_color.update(gebeurtenis)
            detectie_event.set()
        
        self.device_manager.zet_detectie_callback(on_detectie)
        await self.device_manager.start_alle()
        
        for ronde in range(1, aantal_rondes + 1):
            if self.stop_event.is_set():
                logger.info("Game gestopt door gebruiker")
                break
            
            gekozen_kleur = random.choice(kleuren).upper()
            
            await self.sio.emit('vallende_kleur_start', {
                'rondenummer': ronde,
                'maxronden': aantal_rondes,
                'kleur': gekozen_kleur,
                'val_tijd': val_tijd
            })
            logger.info(f"Round {ronde}: Falling color = {gekozen_kleur}, Fall time = {val_tijd}s")
            
            await asyncio.sleep(0.2)
            await self.device_manager.set_correct_kegel(gekozen_kleur)
            
            detectie_event.clear()
            detected_color.clear()
            starttijd = time.time()
            correct_touched = False
            status = "te laat"  # Default status als tijd op is
            
            try:
                # Start falling loop
                while True:
                    elapsed = time.time() - starttijd
                    
                    if elapsed >= val_tijd:
                        # Tijd is op, kleur op 100%, speler is dood
                        percentage = 100
                        await self.sio.emit('vallende_kleur_percentage', {
                            'percentage': percentage,
                            'rondenummer': ronde
                        })
                        status = "te laat"
                        await self.sio.emit('fout_kleur', {'status': 'game over - te laat'})
                        logger.info(f"Game Over! Kleur bereikte 100%")
                        break
                    
                    # Bereken percentage (0% -> 100%)
                    percentage = min(100, (elapsed / val_tijd * 100))
                    
                    await self.sio.emit('vallende_kleur_percentage', {
                        'percentage': round(percentage, 1),
                        'rondenummer': ronde
                    })
                    
                    # Check of er een detectie is
                    if detectie_event.is_set():
                        reactietijd = round(elapsed, 2) - self.hardware_delay
                        detected_kleur = detected_color.get("kleur", "").lower()
                        
                        if detected_kleur == gekozen_kleur.lower():
                            status = "correct"
                            correct_touched = True
                            logger.info(f"Correct! Reaction time: {reactietijd}s at {percentage:.1f}%")
                            break
                        else:
                            status = "fout"
                            await self.sio.emit('fout_kleur', {'status': 'game over - foute kleur'})
                            logger.info(f"Wrong color! Detected: {detected_kleur}, Expected: {gekozen_kleur}")
                            break
                    
                    # Check of game gestopt is
                    if self.stop_event.is_set():
                        logger.info("Game gestopt tijdens falling color")
                        status = "gestopt"
                        break
                    
                    await asyncio.sleep(update_interval)
                
            except Exception as e:
                logger.error(f"Error in fallingcolorgame ronde: {e}")
                status = "fout"
            
            # Bereken reactietijd voor opslag
            eindtijd = time.time()
            reactietijd = round(eindtijd - starttijd, 2) - self.hardware_delay
            
            fallingcolor_rondes.append({
                "rondenummer": ronde,
                "waarde": reactietijd if status == "correct" else val_tijd,
                "uitkomst": status,
            })
            
            await self.device_manager.reset_correct_kegel(gekozen_kleur)
            
            # Als de speler dood is (fout of te laat), stop de game
            if status in ["fout", "te laat"]:
                logger.info(f"Speler is dood na ronde {ronde}")
                break
        
        await self.device_manager.stop_alle()
        self.device_manager.zet_detectie_callback(None)
        await self.sio.emit('game_einde', {"status": "game gedaan"})
        
        return fallingcolor_rondes
    
    def reset_stop_event(self):
        """Reset het stop event voor een nieuwe game"""
        self.stop_event.clear()
    
    def stop_game(self):
        """Zet het stop event om de game te stoppen"""
        self.stop_event.set()