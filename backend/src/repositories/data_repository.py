from typing import List, Optional, Any, Dict
from backend.src.database import Database
from backend.src.models.models import (
    RondeWaarde,
    Training,
    GameVoorOverzicht,
    DetailGame,
    Moeilijkheid,
    Ronde,
    LeaderboardItem
)

class DataRepository:
    
    @staticmethod
    def add_gebruiker(gebruikersnaam: str) -> Any:
        sql_query = "INSERT INTO Gebruikers (Gebruikersnaam, LaatstBewerkt) VALUES (?, datetime('now'))"
        params = (gebruikersnaam,)
        return Database.execute_sql(sql_query, params)

    @staticmethod
    def add_training(training: Training) -> Any:
        sql_query = """
            INSERT INTO Trainingen 
            (Start, AantalKleuren, GebruikersId, RondeId, MoeilijkheidsId, GameId) 
            VALUES (?, ?, ?, ?, ?, ?)
        """
        params = (training.start_tijd, training.aantal_kleuren, training.gebruikers_id, training.ronde_id, training.moeilijkheids_id, training.game_id)
        return Database.execute_sql(sql_query, params)

    @staticmethod
    def add_ronde_waarde(ronde_waarde: RondeWaarde) -> Any:
        sql_query = """
            INSERT INTO RondeWaarden (TrainingsId, RondeNummer, Waarde, Uitkomst) 
            VALUES (?, ?, ?, ?)
        """
        params = (ronde_waarde.trainings_id, ronde_waarde.ronde_nummer, ronde_waarde.waarde, ronde_waarde.uitkomst)
        return Database.execute_sql(sql_query, params)

    @staticmethod
    def get_last_rondewaarden_from_last_training() -> List[RondeWaarde]:
        sql_query = """
        SELECT * FROM RondeWaarden
        WHERE TrainingsId = (
            SELECT MAX(TrainingsId) FROM Trainingen
        )
        """
        rows = Database.get_rows(sql_query)
        
        result_list = []
        if rows is None:
            return result_list
        
        for row in rows:
            item = RondeWaarde(
                trainings_id=row['TrainingsId'],
                ronde_nummer=row['RondeNummer'],
                waarde=row['Waarde'],
                uitkomst=row['Uitkomst']
            )
            result_list.append(item)
            
        return result_list

    @staticmethod
    def get_ranking_for_onetraining(trainings_id: int) -> Optional[int]:
        sql_avg = "SELECT AVG(Waarde) as avg_w FROM RondeWaarden WHERE TrainingsId = ?"
        row = Database.get_one_row(sql_avg, (trainings_id,))
        
        if not row or row.get('avg_w') is None:
            return None
            
        target_avg = row.get('avg_w')

        sql_count = """
            SELECT COUNT(*) as cnt FROM (
                SELECT TrainingsId, AVG(Waarde) as avg_w 
                FROM RondeWaarden 
                GROUP BY TrainingsId
            ) AS sub WHERE avg_w < ?
        """
        count_row = Database.get_one_row(sql_count, (target_avg,))
        
        if not count_row:
            return None
            
        plaats = count_row.get('cnt', 0) + 1
        return plaats

    @staticmethod
    def get_last_training_id() -> Optional[int]:
        sql_query = "SELECT MAX(TrainingsId) as last_id FROM Trainingen"
        row = Database.get_one_row(sql_query)
        
        if row and row.get('last_id'):
            return row.get('last_id')
        return None
    
    @staticmethod
    def get_all_games() -> List[Dict]:
        """Haal alle games op zonder highscore berekening"""
        sql_query = "SELECT GameId, GameNaam, Tag, Eenheid FROM Games"
        rows = Database.get_rows(sql_query)
        return rows if rows else []
    
    @staticmethod
    def get_best_avg_for_game(game_id: int, use_min: bool = False) -> float:
        """Haal de beste gemiddelde score op voor een game
        
        Args:
            game_id: ID van de game
            use_min: True voor laagste (Color Sprint), False voor hoogste (andere games)
        """
        agg_func = "MIN" if use_min else "MAX"
        sql_query = f"""
        SELECT {agg_func}(avg_waarde) as best_score
        FROM (
            SELECT AVG(rw.Waarde) as avg_waarde
            FROM Trainingen t
            JOIN RondeWaarden rw ON t.TrainingsId = rw.TrainingsId
            WHERE t.GameId = ?
            GROUP BY t.TrainingsId
        )
        """
        row = Database.get_one_row(sql_query, (game_id,))
        return row.get('best_score', 0) if row and row.get('best_score') is not None else 0
    
    @staticmethod
    def get_max_kleuren_for_game(game_id: int) -> int:
        """Haal het hoogste aantal kleuren op voor een game (voor Memory)"""
        sql_query = "SELECT MAX(AantalKleuren) as max_kleuren FROM Trainingen WHERE GameId = ?"
        row = Database.get_one_row(sql_query, (game_id,))
        return row.get('max_kleuren', 0) if row and row.get('max_kleuren') is not None else 0
    
    @staticmethod
    def get_game_details(game_id: int) -> DetailGame:
        """Haal de details van een game op, inclusief moeilijkheden en rondes"""
        sql_moeilijkheden = "SELECT MoeilijkheidsId, Moeilijkheid, Snelheid FROM Moeilijkheden WHERE GameId = ?"
        rows_moeilijkheden = Database.get_rows(sql_moeilijkheden, (game_id,))
        
        sql_rondes = "SELECT RondeId, Nummer FROM Rondes WHERE GameId = ?"
        rows_rondes = Database.get_rows(sql_rondes, (game_id,))
        
        sql_game = "SELECT GameNaam, GameBeschrijving FROM Games WHERE GameId = ?"
        row_game = Database.get_one_row(sql_game, (game_id,))
        
        # Haal leaderboard op
        sql_leaderboard = """
        SELECT 
            ROW_NUMBER() OVER (ORDER BY AVG(rv.Waarde) ASC) as plaats,
            g.Gebruikersnaam,
            AVG(rv.Waarde) as waarde
        FROM Trainingen t
        JOIN Gebruikers g ON t.GebruikersId = g.GebruikersId
        JOIN RondeWaarden rv ON t.TrainingsId = rv.TrainingsId
        WHERE t.GameId = ?
        GROUP BY g.GebruikersId, g.Gebruikersnaam
        ORDER BY waarde ASC
        LIMIT 3
        """
        rows_leaderboard = Database.get_rows(sql_leaderboard, (game_id,))
        
        list_moeilijkheden = [Moeilijkheid(moeilijkheid=row['Moeilijkheid'], snelheid=row['Snelheid'], moeilijkheid_id=row['MoeilijkheidsId']) for row in rows_moeilijkheden] if rows_moeilijkheden else []
        list_rondes = [Ronde(ronde_id=row['RondeId'], nummer=row['Nummer']) for row in rows_rondes] if rows_rondes else []
        game_naam = row_game['GameNaam'] if row_game and 'GameNaam' in row_game else ""
        leaderboard = [LeaderboardItem(plaats=row['plaats'], gebruikersnaam=row['Gebruikersnaam'], waarde=round(row['waarde'], 2)) for row in rows_leaderboard] if rows_leaderboard else []
        
        return DetailGame(
            list_moeilijkheden=list_moeilijkheden,
            aantal_rondes=list_rondes,
            game_naam=game_naam,
            game_beschrijving=row_game['GameBeschrijving'] if row_game and 'GameBeschrijving' in row_game else "",
            leaderboard=leaderboard
        )
    
    @staticmethod
    def get_leaderboard_for_game(game_id: int, top_n: int = 10) -> List[LeaderboardItem]:
        """Haal de leaderboard op voor een specifieke game"""
        sql_query = """
        SELECT 
            ROW_NUMBER() OVER (ORDER BY AVG(rv.Waarde) ASC) as plaats,
            g.Gebruikersnaam,
            AVG(rv.Waarde) as waarde
        FROM Trainingen t
        JOIN Gebruikers g ON t.GebruikersId = g.GebruikersId
        JOIN RondeWaarden rv ON t.TrainingsId = rv.TrainingsId
        WHERE t.GameId = ?
        GROUP BY g.GebruikersId, g.Gebruikersnaam
        ORDER BY waarde ASC
        LIMIT ?
        """
        rows = Database.get_rows(sql_query, (game_id, top_n))
        
        leaderboard = []
        if rows:
            for row in rows:
                item = LeaderboardItem(
                    plaats=row['plaats'],
                    gebruikersnaam=row['Gebruikersnaam'],
                    waarde=round(row['waarde'], 2)
                )
                leaderboard.append(item)
        
        return leaderboard
