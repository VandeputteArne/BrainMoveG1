from typing import List, Optional, Any, Dict
from backend.src.database import Database
from backend.src.models.models import (
    MoeilijkheidVoorLeaderboard,
    RondeWaarde,
    Training,
    GameVoorOverzicht,
    DetailGame,
    Moeilijkheid,
    Ronde,
    LeaderboardItem,
    GameVoorFilter,
    TrainingVoorHistorie
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
        # Haal eerst de game_id en moeilijkheidsgraad op voor deze training
        sql_training = "SELECT GameId, MoeilijkheidsId FROM Trainingen WHERE TrainingsId = ?"
        training_row = Database.get_one_row(sql_training, (trainings_id,))
        
        if not training_row:
            return None
        
        game_id = training_row.get('GameId')
        moeilijkheids_id = training_row.get('MoeilijkheidsId')
        
        # Voor Memory (game_id = 2): ranking op basis van hoogste RondeNummer, dan gemiddelde waarde
        if game_id == 2:
            # Haal het hoogste RondeNummer en gemiddelde waarde voor deze training op
            sql_stats = """
                SELECT MAX(RondeNummer) as max_ronde, AVG(Waarde) as avg_waarde
                FROM RondeWaarden
                WHERE TrainingsId = ?
            """
            stats_row = Database.get_one_row(sql_stats, (trainings_id,))
            
            if not stats_row or stats_row.get('max_ronde') is None:
                return None
            
            max_ronde = stats_row.get('max_ronde')
            avg_waarde = stats_row.get('avg_waarde')
            
            # Tel hoeveel trainingen beter zijn (hoger max_ronde OF gelijk max_ronde maar lager avg_waarde)
            # Filter op dezelfde moeilijkheidsgraad
            sql_count = """
                SELECT COUNT(*) as cnt FROM (
                    SELECT MAX(rv.RondeNummer) as max_ronde, AVG(rv.Waarde) as avg_waarde
                    FROM Trainingen t
                    JOIN RondeWaarden rv ON t.TrainingsId = rv.TrainingsId
                    WHERE t.GameId = ? AND t.MoeilijkheidsId = ?
                    GROUP BY t.TrainingsId
                ) AS sub 
                WHERE max_ronde > ? OR (max_ronde = ? AND avg_waarde < ?)
            """
            count_row = Database.get_one_row(sql_count, (game_id, moeilijkheids_id, max_ronde, max_ronde, avg_waarde))
            
            if not count_row:
                return None
            
            plaats = count_row.get('cnt', 0) + 1
            return plaats
        
        # Voor andere games: ranking op basis van gemiddelde waarde (lager is beter)
        # GEEN filter op moeilijkheidsgraad
        else:
            sql_avg = "SELECT AVG(Waarde) as avg_w FROM RondeWaarden WHERE TrainingsId = ?"
            row = Database.get_one_row(sql_avg, (trainings_id,))
            
            if not row or row.get('avg_w') is None:
                return None
                
            target_avg = row.get('avg_w')

            sql_count = """
                SELECT COUNT(*) as cnt FROM (
                    SELECT t.TrainingsId, AVG(rv.Waarde) as avg_w 
                    FROM Trainingen t
                    JOIN RondeWaarden rv ON t.TrainingsId = rv.TrainingsId
                    WHERE t.GameId = ?
                    GROUP BY t.TrainingsId
                ) AS sub WHERE avg_w < ?
            """
            count_row = Database.get_one_row(sql_count, (game_id, target_avg))
            
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
        
        sql_game = "SELECT GameNaam, GameBeschrijving, Eenheid FROM Games WHERE GameId = ?"
        row_game = Database.get_one_row(sql_game, (game_id,))
        eenheid = row_game.get('Eenheid', '') if row_game else ''
        
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
        leaderboard = [LeaderboardItem(plaats=row['plaats'], gebruikersnaam=row['Gebruikersnaam'], waarde=round(row['waarde'], 2), eenheid=eenheid) for row in rows_leaderboard] if rows_leaderboard else []
        
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
        # Haal eenheid op voor deze game
        sql_eenheid = "SELECT Eenheid FROM Games WHERE GameId = ?"
        eenheid_row = Database.get_one_row(sql_eenheid, (game_id,))
        eenheid = eenheid_row.get('Eenheid', '') if eenheid_row else ''
        
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
                    waarde=round(row['waarde'], 2),
                    eenheid=eenheid
                )
                leaderboard.append(item)
        
        return leaderboard
    
    #historie functies
    @staticmethod
    def get_games_for_filter() -> List[GameVoorFilter]:
        """Haal alle games op voor filter doeleinden"""
        sql_query = "SELECT GameId, GameNaam FROM Games"
        rows = Database.get_rows(sql_query)
        
        games = []
        if rows:
            for row in rows:
                game = GameVoorFilter(
                    game_id=row['GameId'],
                    game_naam=row['GameNaam']
                )
                games.append(game)
        
        return games
    
    @staticmethod
    def get_trainingen_with_filters(game_id: int, datum: Optional[str], gebruikersnaam: Optional[str]) -> List['TrainingVoorHistorie']:
        """Haal trainingen op met optionele filters voor datum en gebruikersnaam"""
        
        # Voor Memory (game_id = 2): gebruik AantalKleuren
        # Voor andere games: gebruik gemiddelde van Waarde
        if game_id == 2:
            sql_query = """
            SELECT 
                t.TrainingsId, 
                t.Start, 
                g.Gebruikersnaam,
                t.AantalKleuren as waarde,
                ga.Eenheid
            FROM Trainingen t
            JOIN Gebruikers g ON t.GebruikersId = g.GebruikersId
            JOIN Games ga ON t.GameId = ga.GameId
            WHERE t.GameId = ?
            """
        else:
            sql_query = """
            SELECT 
                t.TrainingsId, 
                t.Start, 
                g.Gebruikersnaam,
                ROUND(AVG(rv.Waarde), 2) as waarde,
                ga.Eenheid
            FROM Trainingen t
            JOIN Gebruikers g ON t.GebruikersId = g.GebruikersId
            JOIN RondeWaarden rv ON t.TrainingsId = rv.TrainingsId
            JOIN Games ga ON t.GameId = ga.GameId
            WHERE t.GameId = ?
            """
        
        params = [game_id]
        
        if datum:
            # Converteer dd-mm-yyyy of dd-mm-yy naar yyyy-mm-dd voor SQLite
            from datetime import datetime
            try:
                # Probeer eerst dd-mm-yyyy formaat (4-cijferig jaar)
                datum_obj = datetime.strptime(datum, "%d-%m-%Y")
                datum_iso = datum_obj.strftime("%Y-%m-%d")
            except ValueError:
                try:
                    # Probeer dd-mm-yy formaat (2-cijferig jaar)
                    datum_obj = datetime.strptime(datum, "%d-%m-%y")
                    datum_iso = datum_obj.strftime("%Y-%m-%d")
                except ValueError:
                    try:
                        # Probeer yyyy-mm-dd formaat (ISO/Postman)
                        datum_obj = datetime.strptime(datum, "%Y-%m-%d")
                        datum_iso = datum
                    except ValueError:
                        # Als alles faalt, gebruik originele waarde
                        datum_iso = datum
            
            sql_query += " AND DATE(t.Start) = DATE(?)"
            params.append(datum_iso)
        
        if gebruikersnaam:
            sql_query += " AND LOWER(g.Gebruikersnaam) LIKE LOWER(?)"
            params.append(f"%{gebruikersnaam}%")
        
        # Voor Memory: geen GROUP BY nodig, voor andere games wel
        if game_id == 2:
            sql_query += " ORDER BY t.Start DESC"
        else:
            sql_query += " GROUP BY t.TrainingsId, t.Start, g.Gebruikersnaam, ga.Eenheid ORDER BY t.Start DESC"
        
        rows = Database.get_rows(sql_query, tuple(params))
        
        trainingen = []
        if rows:
            from backend.src.models.models import TrainingVoorHistorie
            for row in rows:
                training = TrainingVoorHistorie(
                    training_id=row['TrainingsId'],
                    start_tijd=row['Start'],
                    gebruikersnaam=row['Gebruikersnaam'],
                    waarde=float(row['waarde']),
                    eenheid=row['Eenheid']
                )
                trainingen.append(training)
        
        return trainingen

    @staticmethod
    def get_allerondewaarden_by_trainingsId(trainings_id: int) -> List[RondeWaarde]:
        """Haal alle rondewaarden op voor een specifieke training"""
        sql_query = "SELECT * FROM RondeWaarden WHERE TrainingsId = ? ORDER BY RondeNummer ASC"
        rows = Database.get_rows(sql_query, (trainings_id,))
        
        rondewaarden = []
        if rows:
            for row in rows:
                rondewaarde = RondeWaarde(
                    trainings_id=row['TrainingsId'],
                    ronde_nummer=row['RondeNummer'],
                    waarde=row['Waarde'],
                    uitkomst=row['Uitkomst']
                )
                rondewaarden.append(rondewaarde)
        
        return rondewaarden
    

    @staticmethod
    def get_moeilijkheden_for_game(game_id: int) -> List[MoeilijkheidVoorLeaderboard]:
        """Haal alle moeilijkheden op voor een specifieke game"""
        sql_query = "SELECT MoeilijkheidsId, Moeilijkheid FROM Moeilijkheden WHERE GameId = ?"
        rows = Database.get_rows(sql_query, (game_id,))
        
        moeilijkheden = []
        if rows:
            for row in rows:
                moeilijkheid = MoeilijkheidVoorLeaderboard(
                    moeilijkheid_id=row['MoeilijkheidsId'],
                    moeilijkheid=row['Moeilijkheid']
                )
                moeilijkheden.append(moeilijkheid)
        
        return moeilijkheden
    

    @staticmethod
    def get_leaderboard_with_filters(game_id: int, moeilijkheids_id: Optional[int] = None) -> List[LeaderboardItem]:
        """Haal de leaderboard op voor een specifieke game met optionele moeilijkheidsfilter"""
        
        # Haal eenheid op voor deze game
        sql_eenheid = "SELECT Eenheid FROM Games WHERE GameId = ?"
        eenheid_row = Database.get_one_row(sql_eenheid, (game_id,))
        eenheid = eenheid_row.get('Eenheid', '') if eenheid_row else ''
        
        # Voor Memory (game_id = 2): sorteer eerst op hoogste RondeNummer (DESC), dan op gemiddelde waarde (ASC)
        if game_id == 2:
            moeilijkheids_filter = ""
            params = [game_id]
            if moeilijkheids_id is not None:
                moeilijkheids_filter = " AND t.MoeilijkheidsId = ?"
                params.append(moeilijkheids_id)
            
            sql_query = f"""
            SELECT 
                ROW_NUMBER() OVER (ORDER BY beste_kleuren DESC, gem_waarde ASC) as plaats,
                Gebruikersnaam,
                beste_kleuren as waarde
            FROM (
                SELECT 
                    g.Gebruikersnaam,
                    MAX(rondes_per_training.max_ronde) as beste_kleuren,
                    AVG(rv.Waarde) as gem_waarde
                FROM Gebruikers g
                JOIN Trainingen t ON g.GebruikersId = t.GebruikersId
                LEFT JOIN (
                    SELECT TrainingsId, MAX(RondeNummer) as max_ronde
                    FROM RondeWaarden
                    GROUP BY TrainingsId
                ) rondes_per_training ON t.TrainingsId = rondes_per_training.TrainingsId
                LEFT JOIN RondeWaarden rv ON t.TrainingsId = rv.TrainingsId
                WHERE t.GameId = ?{moeilijkheids_filter}
                GROUP BY g.GebruikersId, g.Gebruikersnaam
            ) ranked
            ORDER BY beste_kleuren DESC, gem_waarde ASC
            LIMIT 10
            """
        else:
            # Voor andere games: sorteer alleen op gemiddelde waarde (ASC)
            sql_query = """
            SELECT 
                ROW_NUMBER() OVER (ORDER BY AVG(rv.Waarde) ASC) as plaats,
                g.Gebruikersnaam,
                AVG(rv.Waarde) as waarde
            FROM Trainingen t
            JOIN Gebruikers g ON t.GebruikersId = g.GebruikersId
            JOIN RondeWaarden rv ON t.TrainingsId = rv.TrainingsId
            WHERE t.GameId = ?
            """
            params = [game_id]
            
            if moeilijkheids_id is not None:
                sql_query += " AND t.MoeilijkheidsId = ?"
                params.append(moeilijkheids_id)
            
            sql_query += """
            GROUP BY g.GebruikersId, g.Gebruikersnaam
            ORDER BY waarde ASC
            LIMIT 10
            """
        
        rows = Database.get_rows(sql_query, tuple(params))
        
        leaderboard = []
        if rows:
            for row in rows:
                item = LeaderboardItem(
                    plaats=row['plaats'],
                    gebruikersnaam=row['Gebruikersnaam'],
                    waarde=round(row['waarde'], 2),
                    eenheid=eenheid
                )
                leaderboard.append(item)
        
        return leaderboard
    
    @staticmethod
    def get_gameid_by_trainingid(training_id: int) -> Optional[int]:
        """Haal de GameId op voor een specifieke training"""
        sql_query = "SELECT GameId FROM Trainingen WHERE TrainingsId = ?"
        row = Database.get_one_row(sql_query, (training_id,))
        
        if row and 'GameId' in row:
            return row['GameId']
        return None
    
    @staticmethod
    def get_totale_aantal_rondes_by_rondeid(ronde_id: int):
        """Haal het totale aantal rondes op voor een specifieke ronde ID"""
        sql_query = "SELECT Nummer as totaal FROM Rondes WHERE RondeId = ?"
        row = Database.get_one_row(sql_query, (ronde_id,))
        
        if row and 'totaal' in row:
            return row['totaal']
        return 0
    
    @staticmethod
    def get_totale_aantal_rondes_by_trainingid(training_id: int):
        """Haal het totale aantal rondes op voor een specifieke training ID"""
        sql_query = """
            SELECT r.Nummer as totaal 
            FROM Rondes r
            INNER JOIN Trainingen t ON t.RondeId = r.RondeId
            WHERE t.TrainingsId = ?
        """
        row = Database.get_one_row(sql_query, (training_id,))
        
        if row and 'totaal' in row:
            return row['totaal']
        return 0
    
    @staticmethod
    def get_gebruikersnaam_by_trainingid(training_id: int) -> Optional[str]:
        """Haal de gebruikersnaam op voor een specifieke training ID"""
        sql_query = """
            SELECT g.Gebruikersnaam 
            FROM Gebruikers g
            INNER JOIN Trainingen t ON t.GebruikersId = g.GebruikersId
            WHERE t.TrainingsId = ?
        """
        row = Database.get_one_row(sql_query, (training_id,))
        
        if row and 'Gebruikersnaam' in row:
            return row['Gebruikersnaam']
        return None
