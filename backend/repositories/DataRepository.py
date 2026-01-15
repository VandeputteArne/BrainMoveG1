from .Database import Database
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
