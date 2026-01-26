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
    
    async def run_colorbattle(self,aantal_rondes: int,kleuren: List[str],snelheid: float,speler1_naam: str,speler2_naam: str) -> Dict:
        """Voert het Color Battle game uit met 2 spelers"""
        rondes_resultaten = []
        max_tijd = float(snelheid)

        # Track scores
        speler1_correct = 0
        speler2_correct = 0
        speler1_totaal_tijd = 0.0
        speler2_totaal_tijd = 0.0

        # Detection state for handling 2 touches per round
        detecties = []
        detectie_event = asyncio.Event()

        def on_detectie(gebeurtenis):
            detecties.append({
                "kleur": gebeurtenis.get("kleur", "").lower(),
                "tijd": time.time()
            })
            detectie_event.set()  # Signal that a new detection arrived

        self.device_manager.zet_detectie_callback(on_detectie)
        await self.device_manager.start_alle()

        # Emit game start with player names
        await self.sio.emit('colorbattle_start', {
            'speler1_naam': speler1_naam,
            'speler2_naam': speler2_naam,
            'aantal_rondes': aantal_rondes
        })

        for ronde in range(1, aantal_rondes + 1):
            if self.stop_event.is_set():
                logger.info("Game gestopt door gebruiker")
                break

            # Pick 2 different colors for each player
            beschikbare_kleuren = [k.lower() for k in kleuren]
            random.shuffle(beschikbare_kleuren)
            speler1_kleur = beschikbare_kleuren[0].upper()
            speler2_kleur = beschikbare_kleuren[1].upper()

            # Emit round start with colors
            await self.sio.emit('colorbattle_ronde', {
                'rondenummer': ronde,
                'maxronden': aantal_rondes,
                'speler1_kleur': speler1_kleur,
                'speler2_kleur': speler2_kleur
            })
            logger.info(f"Round {ronde}: Player1={speler1_kleur}, Player2={speler2_kleur}")

            await asyncio.sleep(0.2)

            # Set both cones as "correct" for detection
            await self.device_manager.set_correct_kegel(speler1_kleur)
            await self.device_manager.set_correct_kegel(speler2_kleur)

            # Reset detection state
            detecties.clear()
            detectie_event.clear()
            starttijd = time.time()

            # Initialize round results
            speler1_tijd = max_tijd
            speler2_tijd = max_tijd
            speler1_uitkomst = "te laat"
            speler2_uitkomst = "te laat"
            speler1_touch_tijd = None
            speler2_touch_tijd = None

            try:
                # Wait until both players have results, or timeout/stop
                while speler1_touch_tijd is None or speler2_touch_tijd is None:
                    if self.stop_event.is_set():
                        logger.info("Game gestopt tijdens wachten op detectie")
                        break

                    elapsed = time.time() - starttijd

                    # Check for new detection
                    remaining = max_tijd - elapsed
                    try:
                        await asyncio.wait_for(
                            detectie_event.wait(),
                            timeout=min(0.1, remaining)
                        )
                        # Clear event so we wait for the next detection
                        detectie_event.clear()
                    except asyncio.TimeoutError:
                        pass

                    # Process any detections we have
                    # Note: Hardware has 500ms cooldown per cone, so no software bounce filter needed
                    for det in detecties:
                        det_kleur = det["kleur"]
                        det_tijd = det["tijd"] - starttijd - self.hardware_delay

                        # Speler 1's kleur aangeraakt
                        if det_kleur == speler1_kleur.lower():
                            if speler1_touch_tijd is None:
                                # Speler 1 raakt zijn eigen kleur aan = correct
                                speler1_touch_tijd = det_tijd
                                speler1_tijd = round(max(0, det_tijd), 2)
                                speler1_uitkomst = "correct"
                                logger.info(f"Player1 touched {det_kleur} (correct) at {speler1_tijd}s")
                            elif speler2_touch_tijd is None:
                                # Speler 2 raakt speler 1's kleur aan = fout
                                speler2_touch_tijd = det_tijd
                                speler2_tijd = round(max_tijd + max(0, det_tijd), 2)
                                speler2_uitkomst = "te laat"
                                logger.info(f"Player2 touched {det_kleur} (wrong) at {det_tijd:.2f}s")

                        # Speler 2's kleur aangeraakt
                        elif det_kleur == speler2_kleur.lower():
                            if speler2_touch_tijd is None:
                                # Speler 2 raakt zijn eigen kleur aan = correct
                                speler2_touch_tijd = det_tijd
                                speler2_tijd = round(max(0, det_tijd), 2)
                                speler2_uitkomst = "correct"
                                logger.info(f"Player2 touched {det_kleur} (correct) at {speler2_tijd}s")
                            elif speler1_touch_tijd is None:
                                # Speler 1 raakt speler 2's kleur aan = fout
                                speler1_touch_tijd = det_tijd
                                speler1_tijd = round(max_tijd + max(0, det_tijd), 2)
                                speler1_uitkomst = "te laat"
                                logger.info(f"Player1 touched {det_kleur} (wrong) at {det_tijd:.2f}s")

                        # Andere kleur aangeraakt (niet van speler 1 of 2)
                        else:
                            if speler1_touch_tijd is None:
                                # Attribute to speler 1 = fout
                                speler1_touch_tijd = det_tijd
                                speler1_tijd = round(max_tijd + max(0, det_tijd), 2)
                                speler1_uitkomst = "te laat"
                                logger.info(f"Player1 touched {det_kleur} (wrong) at {det_tijd:.2f}s")
                            elif speler2_touch_tijd is None:
                                # Attribute to speler 2 = fout
                                speler2_touch_tijd = det_tijd
                                speler2_tijd = round(max_tijd + max(0, det_tijd), 2)
                                speler2_uitkomst = "te laat"
                                logger.info(f"Player2 touched {det_kleur} (wrong) at {det_tijd:.2f}s")

                        

            except Exception as e:
                logger.error(f"Error in colorbattle ronde: {e}")

            # Determine round winner
            ronde_winnaar = None
            if speler1_uitkomst == "correct" and speler2_uitkomst == "correct":
                if speler1_touch_tijd < speler2_touch_tijd:
                    ronde_winnaar = 1
                elif speler2_touch_tijd < speler1_touch_tijd:
                    ronde_winnaar = 2
                # else: tie (ronde_winnaar stays None)
            elif speler1_uitkomst == "correct":
                ronde_winnaar = 1
            elif speler2_uitkomst == "correct":
                ronde_winnaar = 2
            # else: both wrong/late, no winner

            # Update totals
            if speler1_uitkomst == "correct":
                speler1_correct += 1
            if speler2_uitkomst == "correct":
                speler2_correct += 1
            speler1_totaal_tijd += speler1_tijd
            speler2_totaal_tijd += speler2_tijd

            ronde_resultaat = {
                "rondenummer": ronde,
                "speler1_kleur": speler1_kleur,
                "speler2_kleur": speler2_kleur,
                "speler1_tijd": speler1_tijd,
                "speler2_tijd": speler2_tijd,
                "speler1_uitkomst": speler1_uitkomst,
                "speler2_uitkomst": speler2_uitkomst,
                "ronde_winnaar": ronde_winnaar
            }
            rondes_resultaten.append(ronde_resultaat)

            ronde_resultaat_voor_emit = {
                "speler1_uitkomst": speler1_uitkomst,
                "speler2_uitkomst": speler2_uitkomst,
            }

            # Emit round result
            await self.sio.emit('colorbattle_ronde_einde', ronde_resultaat_voor_emit)
            await asyncio.sleep(1)  # Small delay to allow frontend processing

            # Reset cones
            await self.device_manager.reset_correct_kegel(speler1_kleur)
            await self.device_manager.reset_correct_kegel(speler2_kleur)

            if self.stop_event.is_set():
                break

        await self.device_manager.stop_alle()
        self.device_manager.zet_detectie_callback(None)

        # Determine overall winner
        winnaar = None
        if speler1_correct > speler2_correct:
            winnaar = 1
        elif speler2_correct > speler1_correct:
            winnaar = 2
        elif speler1_totaal_tijd < speler2_totaal_tijd:
            winnaar = 1
        elif speler2_totaal_tijd < speler1_totaal_tijd:
            winnaar = 2
        # else: complete tie

        eind_resultaat = {
            "speler1_naam": speler1_naam,
            "speler2_naam": speler2_naam,
            "speler1_correct": speler1_correct,
            "speler2_correct": speler2_correct,
            "speler1_totaal_tijd": round(speler1_totaal_tijd, 2),
            "speler2_totaal_tijd": round(speler2_totaal_tijd, 2),
            "winnaar": winnaar,
            "rondes": rondes_resultaten
        }

        await self.sio.emit('colorbattle_einde', eind_resultaat)
        logger.info(f"Color Battle ended. Winner: Player {winnaar}")

        return eind_resultaat

    def reset_stop_event(self):
        """Reset het stop event voor een nieuwe game"""
        self.stop_event.clear()

    def stop_game(self):
        """Zet het stop event om de game te stoppen"""
        self.stop_event.set()