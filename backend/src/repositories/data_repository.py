from typing import List, Optional, Any
from backend.src.database import Database
from backend.src.models.models import (
    RondeWaarde,
    Instellingen,
    Resultaat
)

class DataRepository:
    
    @staticmethod
    def add_gebruiker(gebruikersnaam: str) -> Any:
        sql_query = "INSERT INTO Gebruikers (Gebruikersnaam, LaatstBewerkt) VALUES (?, datetime('now'))"
        params = (gebruikersnaam,)
        return Database.execute_sql(sql_query, params)

    @staticmethod
    def add_training(start_tijd: str, aantal_kleuren: int, gebruikers_id: int, 
                     ronde_id: int, moeilijkheids_id: int, game_id: int) -> Any:
        sql_query = """
            INSERT INTO Trainingen 
            (Start, AantalKleuren, GebruikersId, RondeId, MoeilijkheidsId, GameId) 
            VALUES (?, ?, ?, ?, ?, ?)
        """
        params = (start_tijd, aantal_kleuren, gebruikers_id, ronde_id, moeilijkheids_id, game_id)
        return Database.execute_sql(sql_query, params)

    @staticmethod
    def add_ronde_waarde(trainings_id: int, ronde_nummer: int, waarde: int, uitkomst: str) -> Any:
        sql_query = """
            INSERT INTO RondeWaarden (TrainingsId, RondeNummer, Waarde, Uitkomst) 
            VALUES (?, ?, ?, ?)
        """
        params = (trainings_id, ronde_nummer, waarde, uitkomst)
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