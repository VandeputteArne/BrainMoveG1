import asyncio
import random
import time
from typing import List, Dict

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
                print("Game gestopt door gebruiker")
                break
            
            gekozen_kleur = random.choice(kleuren).upper()
            
            await self.sio.emit('gekozen_kleur', {
                'rondenummer': ronde,
                'maxronden': aantal_rondes,
                'kleur': gekozen_kleur
            })
            print(f"Round {ronde}: Chosen color = {gekozen_kleur}")
            
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
                    print("Game gestopt tijdens wachten op detectie")
                    break
                
                if detectie_task in done:
                    reactietijd = round(time.time() - starttijd, 2) - self.hardware_delay
                    detected_kleur = detected_color.get("kleur", "").lower()
                    
                    if (max_tijd - reactietijd) < 0:
                        reactietijd = max_tijd
                        status = "te laat"
                        print(f"Too late! Reaction time: {reactietijd}s")
                    elif detected_kleur == gekozen_kleur.lower():
                        status = "correct"
                        print(f"Correct! Reaction time: {reactietijd}s")
                    else:
                        status = "fout"
                        reactietijd += max_tijd
                        print(f"Wrong color! Detected: {detected_kleur}, Expected: {gekozen_kleur}")
                else:
                    reactietijd = max_tijd
                    status = "te laat"
                    print(f"Too late! Timeout after {max_tijd}s")
                    
            except Exception as e:
                print(f"Error in colorgame ronde: {e}")
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
                print("Game gestopt door gebruiker")
                break
                
            nieuwe_kleur = random.choice(kleuren)
            geheugen_lijst.append(nieuwe_kleur)
            await self.sio.emit('ronde_start', {'rondenummer': ronde, 'maxronden': aantal_rondes})

            await asyncio.sleep(3)
            await self.sio.emit('wacht_even', {'bericht': 'start'})

            for kleur in geheugen_lijst:
                await self.sio.emit('toon_kleur', {'kleur': kleur.upper()})
                print(kleur)
                await asyncio.sleep(snelheid)

            await self.sio.emit('kleuren_getoond', {'aantal': len(geheugen_lijst)})
            await self.device_manager.start_alle()

            starttijd = time.time()
            status = "correct"

            for verwachte_kleur in geheugen_lijst:
                if self.stop_event.is_set():
                    print("Game gestopt tijdens memory sequence")
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
                    
                    for task in pending:
                        task.cancel()
                    
                    await self.device_manager.reset_correct_kegel(verwachte_kleur)
                    
                    if stop_task in done:
                        print("Game gestopt tijdens wachten op aanraking")
                        status = "gestopt"
                        break
                    
                    if detectie_task in done:
                        detected_kleur = detected_color.get("kleur", "").lower()
                        
                        if detected_kleur != verwachte_kleur.lower():
                            await self.sio.emit('fout_kleur', {'status': 'game over'})
                            status = "fout"
                            print(f"Fout! Verwacht: {verwachte_kleur}, Gekregen: {detected_kleur}")
                            break
                        
                        print(f"Correct: {detected_kleur}")
                    else:
                        await self.sio.emit('fout_kleur', {'status': 'timeout'})
                        status = "fout"
                        print("Timeout: Te lang gewacht op aanraking")
                        break

                except Exception as e:
                    await self.device_manager.reset_correct_kegel(verwachte_kleur)
                    print(f"Error in memory sequence: {e}")
                    status = "fout"
                    break

            eindtijd = time.time()
            reactietijd = round(eindtijd - starttijd, 2)
            await self.sio.emit('ronde_einde', {'ronde': ronde, 'status': status})
            print(f"Ronde {ronde} klaar: {status}")
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
        print("Einde memory game")
        return rondes_memory
    
    def reset_stop_event(self):
        """Reset het stop event voor een nieuwe game"""
        self.stop_event.clear()
    
    def stop_game(self):
        """Zet het stop event om de game te stoppen"""
        self.stop_event.set()