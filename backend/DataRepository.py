from Database import Database
class DataRepository:
    @staticmethod
    def add_gebruiker(gebruikersnaam):
        sqlQuery = "INSERT INTO Gebruikers (gebruikersnaam, laatstbewerkt) VALUES (?, datetime('now'))"
        params = (gebruikersnaam,)
        return Database.execute_sql(sqlQuery, params)
        

    @staticmethod
    def add_training(starttijd,aantalKleuren,gebruikersId,rondeId,moeilijkheidsId,gameId):
        sqlQuery = "INSERT INTO Trainingen (start, aantalKleuren, gebruikersId, rondeId, moeilijkheidsId, gameId) VALUES (?, ?, ?, ?, ?, ?)"
        params = (starttijd,aantalKleuren,gebruikersId,rondeId,moeilijkheidsId,gameId)
        return Database.execute_sql(sqlQuery, params)
    
    @staticmethod
    def add_ronde_waarde(trainingsId,rondeNummer,waarde,uitkomst):
        sqlQuery = "INSERT INTO RondeWaarden (TrainingsId, RondeNummer, Waarde, Uitkomst) VALUES (?, ?, ?, ?)"
        params = (trainingsId,rondeNummer,waarde,uitkomst)
        return Database.execute_sql(sqlQuery, params)
    
    @staticmethod
    def get_last_rondewaarden_from_last_training():
        sqlQuery = """
        SELECT * FROM RondeWaarden
        WHERE TrainingsId = (
            SELECT MAX(TrainingsId) FROM Trainingen
        )
        """
        return Database.get_rows(sqlQuery)

    @staticmethod
    def get_ranking_for_onetraining(trainingId):

        # Haal gemiddelde waarde voor de gevraagde training
        sql_avg = "SELECT AVG(Waarde) as avg_w FROM RondeWaarden WHERE TrainingsId = ?"
        row = Database.get_one_row(sql_avg, (trainingId,))
        if not row or row.get('avg_w') is None:
            return None
        target_avg = row.get('avg_w')

        # Tel hoeveel trainingen een lagere (betere) gemiddelde waarde hebben
        sql_count = (
            "SELECT COUNT(*) as cnt FROM ("
            " SELECT TrainingsId, AVG(Waarde) as avg_w FROM RondeWaarden GROUP BY TrainingsId"
            " ) AS sub WHERE avg_w < ?"
        )
        count_row = Database.get_one_row(sql_count, (target_avg,))
        if not count_row:
            return None
        plaats = count_row.get('cnt', 0) + 1
        return plaats

    @staticmethod
    def get_last_training_id():
        sqlQuery = "SELECT MAX(TrainingsId) as last_id FROM Trainingen"
        row = Database.get_one_row(sqlQuery)
        if row and row.get('last_id'):
            return row.get('last_id')
        return None
