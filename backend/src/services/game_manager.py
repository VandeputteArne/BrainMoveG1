import asyncio
import datetime
import logging
from typing import Optional
from backend.src.services.game_service import GameService
from backend.src.repositories.data_repository import DataRepository
from backend.src.models.models import Training, RondeWaarde

logger = logging.getLogger(__name__)

class GameManager:
    def __init__(self, game_service: GameService, sio):
        self.game_service = game_service
        self.sio = sio
        self.current_task: Optional[asyncio.Task] = None
        
        # Game instellingen
        self.game_id: Optional[int] = None
        self.gebruikersnaam: Optional[str] = None
        self.moeilijkheids_id: Optional[int] = None
        self.snelheid: Optional[float] = None
        self.ronde_id: Optional[int] = None
        self.rondes: Optional[int] = None
        self.kleuren: Optional[list] = None
        self.starttijd: Optional[datetime.datetime] = None

        # Color Battle specific settings
        self.speler1_naam: Optional[str] = None
        self.speler2_naam: Optional[str] = None
    
    def set_instellingen(self, instellingen):
        """Sla game instellingen op"""
        self.game_id = instellingen.game_id
        self.gebruikersnaam = instellingen.gebruikersnaam
        self.moeilijkheids_id = instellingen.moeilijkheids_id
        self.snelheid = instellingen.snelheid
        self.ronde_id = instellingen.ronde_id
        self.rondes = instellingen.rondes
        self.kleuren = instellingen.kleuren
        self.starttijd = datetime.datetime.now()

        logger.info(f"GameManager instellingen opgeslagen: game_id={self.game_id}, rondes={self.rondes}")

    def set_colorbattle_instellingen(self, instellingen):
        """Sla Color Battle instellingen op (2 spelers)"""
        self.game_id = instellingen.game_id
        self.speler1_naam = instellingen.speler1_naam
        self.speler2_naam = instellingen.speler2_naam
        self.moeilijkheids_id = instellingen.moeilijkheids_id
        self.snelheid = instellingen.snelheid
        self.ronde_id = instellingen.ronde_id
        self.rondes = instellingen.rondes
        self.kleuren = instellingen.kleuren
        self.starttijd = datetime.datetime.now()

        logger.info(f"GameManager Color Battle instellingen: speler1={self.speler1_naam}, speler2={self.speler2_naam}, rondes={self.rondes}")
    
    def reset_instellingen(self):
        """Reset alle game instellingen naar None"""
        self.game_id = None
        self.gebruikersnaam = None
        self.moeilijkheids_id = None
        self.snelheid = None
        self.ronde_id = None
        self.rondes = None
        self.kleuren = None
        self.starttijd = None
        self.speler1_naam = None
        self.speler2_naam = None
        logger.info("GameManager instellingen gereset")
    
    async def start_colorgame(self):
        """Start colorgame in de achtergrond"""
        try:
            self.game_service.reset_stop_event()
            
            logger.info(f"Start colorgame met {self.rondes} rondes")
            rondes = await self.game_service.run_colorgame(
                self.rondes, self.kleuren, self.snelheid
            )
            
            await self._save_training_results(rondes, "waarde")
            logger.info("Colorgame afgelopen en opgeslagen")
            
        except Exception as e:
            logger.error(f"Fout in colorgame: {e}")
            await self.sio.emit('game_error', {"error": str(e)})
        finally:
            self.current_task = None
            self.reset_instellingen()
    
    async def start_memorygame(self):
        """Start memorygame in de achtergrond"""
        try:
            self.game_service.reset_stop_event()
            
            logger.info(f"Start memorygame met {self.rondes} rondes")
            rondes = await self.game_service.run_memorygame(
                self.snelheid, self.rondes, self.kleuren
            )
            
            await self._save_training_results(rondes, "reactietijd")
            logger.info("Memorygame afgelopen en opgeslagen")
            
        except Exception as e:
            logger.error(f"Fout in memorygame: {e}")
            await self.sio.emit('game_error', {"error": str(e)})
        finally:
            self.current_task = None
            self.reset_instellingen()
    
    async def start_numbergame(self):
        """Start numbergame in de achtergrond"""
        try:
            self.game_service.reset_stop_event()
            
            logger.info(f"Start numbergame met {self.rondes} rondes")
            rondes = await self.game_service.run_numbergame(
                self.rondes, self.kleuren, self.snelheid
            )
            
            await self._save_training_results(rondes, "waarde")
            logger.info("Numbergame afgelopen en opgeslagen")
            
        except Exception as e:
            logger.error(f"Fout in numbergame: {e}")
            await self.sio.emit('game_error', {"error": str(e)})
        finally:
            self.current_task = None
            self.reset_instellingen()
    
    async def start_fallingcolorgame(self):
        """Start falling color game in de achtergrond"""
        try:
            self.game_service.reset_stop_event()

            logger.info(f"Start falling color game met {self.rondes} rondes")
            rondes = await self.game_service.run_fallingcolorgame(
                self.rondes, self.kleuren, self.snelheid
            )

            await self._save_training_results(rondes, "waarde")
            logger.info("Falling color game afgelopen en opgeslagen")

        except Exception as e:
            logger.error(f"Fout in falling color game: {e}")
            await self.sio.emit('game_error', {"error": str(e)})
        finally:
            self.current_task = None
            self.reset_instellingen()

    async def start_colorbattle(self):
        """Start Color Battle game in de achtergrond (2 spelers)"""
        try:
            self.game_service.reset_stop_event()

            logger.info(f"Start Color Battle: {self.speler1_naam} vs {self.speler2_naam}, {self.rondes} rondes")
            resultaat = await self.game_service.run_colorbattle(
                self.rondes, self.kleuren, self.snelheid,
                self.speler1_naam, self.speler2_naam
            )

            # Save training results for both players
            await self._save_colorbattle_results(resultaat)
            logger.info("Color Battle afgelopen en opgeslagen")

        except Exception as e:
            logger.error(f"Fout in Color Battle: {e}")
            await self.sio.emit('game_error', {"error": str(e)})
        finally:
            self.current_task = None
            self.reset_instellingen()
    
    async def _save_training_results(self, rondes: list, waarde_key: str):
        """Sla trainingsresultaten op in de database"""
        user_id = DataRepository.add_gebruiker(self.gebruikersnaam)
        logger.info(f"Nieuwe gebruiker toegevoegd met ID: {user_id}")

        training_id = DataRepository.add_training(
            Training(
                start_tijd=self.starttijd.isoformat(),
                aantal_kleuren=len(self.kleuren),
                gebruikers_id=user_id,
                ronde_id=self.ronde_id,
                moeilijkheids_id=self.moeilijkheids_id,
                game_id=self.game_id
            )
        )
        logger.info(f"Nieuwe training toegevoegd met ID: {training_id}")

        for ronde in rondes:
            DataRepository.add_ronde_waarde(
                RondeWaarde(
                    trainings_id=training_id,
                    ronde_nummer=ronde["rondenummer"],
                    waarde=ronde[waarde_key],
                    uitkomst=ronde.get("uitkomst") or ronde.get("status")
                )
            )

    async def _save_colorbattle_results(self, resultaat: dict):
        """Sla Color Battle resultaten op voor beide spelers"""
        rondes = resultaat["rondes"]

        # Save player 1
        user1_id = DataRepository.add_gebruiker(self.speler1_naam)
        logger.info(f"Speler 1 toegevoegd met ID: {user1_id}")

        training1_id = DataRepository.add_training(
            Training(
                start_tijd=self.starttijd.isoformat(),
                aantal_kleuren=len(self.kleuren),
                gebruikers_id=user1_id,
                ronde_id=self.ronde_id,
                moeilijkheids_id=self.moeilijkheids_id,
                game_id=self.game_id
            )
        )
        logger.info(f"Training speler 1 toegevoegd met ID: {training1_id}")

        for ronde in rondes:
            DataRepository.add_ronde_waarde(
                RondeWaarde(
                    trainings_id=training1_id,
                    ronde_nummer=ronde["rondenummer"],
                    waarde=ronde["speler1_tijd"],
                    uitkomst=ronde["speler1_uitkomst"]
                )
            )

        # Save player 2
        user2_id = DataRepository.add_gebruiker(self.speler2_naam)
        logger.info(f"Speler 2 toegevoegd met ID: {user2_id}")

        training2_id = DataRepository.add_training(
            Training(
                start_tijd=self.starttijd.isoformat(),
                aantal_kleuren=len(self.kleuren),
                gebruikers_id=user2_id,
                ronde_id=self.ronde_id,
                moeilijkheids_id=self.moeilijkheids_id,
                game_id=self.game_id
            )
        )
        logger.info(f"Training speler 2 toegevoegd met ID: {training2_id}")

        for ronde in rondes:
            DataRepository.add_ronde_waarde(
                RondeWaarde(
                    trainings_id=training2_id,
                    ronde_nummer=ronde["rondenummer"],
                    waarde=ronde["speler2_tijd"],
                    uitkomst=ronde["speler2_uitkomst"]
                )
            )
    
    def is_game_running(self) -> bool:
        """Check of er een game actief is"""
        return self.current_task is not None and not self.current_task.done()
    
    def has_valid_settings(self) -> bool:
        """Check of alle benodigde instellingen zijn gezet"""
        # Color Battle has different required settings
        if self.game_id == 5:
            return all([
                self.game_id is not None,
                self.speler1_naam is not None,
                self.speler2_naam is not None,
                self.moeilijkheids_id is not None,
                self.snelheid is not None,
                self.ronde_id is not None,
                self.rondes is not None,
                self.kleuren is not None and len(self.kleuren) >= 2
            ])

        return all([
            self.game_id is not None,
            self.gebruikersnaam is not None,
            self.moeilijkheids_id is not None,
            self.snelheid is not None,
            self.ronde_id is not None,
            self.rondes is not None,
            self.kleuren is not None and len(self.kleuren) > 0
        ])
    
    async def play_game(self, game_id: int) -> dict:
        """Start een game"""
        if self.is_game_running():
            return {
                "status": "already_running",
                "message": "Er is al een game actief."
            }
        
        if not self.has_valid_settings():
            return {
                "status": "missing_settings",
                "message": "Game instellingen zijn niet compleet. Stel eerst de game in."
            }
        
        if game_id == 1:
            self.current_task = asyncio.create_task(self.start_colorgame())
        elif game_id == 2:
            self.current_task = asyncio.create_task(self.start_memorygame())
        elif game_id == 3:
            self.current_task = asyncio.create_task(self.start_numbergame())
        elif game_id == 4:
            self.current_task = asyncio.create_task(self.start_fallingcolorgame())
        elif game_id == 5:
            self.current_task = asyncio.create_task(self.start_colorbattle())
        else:
            return {
                "status": "error",
                "message": f"Onbekend game_id: {game_id}"
            }
        
        return {
            "status": "started",
            "message": "Game is gestart"
        }
    
    async def stop_game(self) -> dict:
        """Stop de actieve game"""
        if not self.is_game_running():
            return {
                "status": "no_game_running",
                "message": "Er is geen actieve game"
            }
        
        self.game_service.stop_game()
        self.current_task.cancel()
        
        try:
            await self.current_task
        except asyncio.CancelledError:
            logger.info("Game task succesvol geannuleerd")
        finally:
            self.current_task = None
            self.reset_instellingen()
        
        return {"status": "stopped", "message": "Game gestopt"}