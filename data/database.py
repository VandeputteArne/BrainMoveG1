import sqlite3

def create_database():
    conn = sqlite3.connect('brainmove.db')
    cursor = conn.cursor()

    # Zorg dat Foreign Keys werken
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. Tabel: Gebruikers
    # LaatstBewerkt is nu DATETIME
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Gebruikers (
        GebruikersId INTEGER PRIMARY KEY AUTOINCREMENT,
        Gebruikersnaam TEXT NOT NULL,
        LaatstBewerkt DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Tabel: Games
    # LaatstBewerkt is nu DATETIME
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Games (
        GameId INTEGER PRIMARY KEY AUTOINCREMENT,
        GameBeschrijving TEXT,
        GameNaam TEXT NOT NULL,
        Eenheid TEXT,
        Tag TEXT,
        LaatstBewerkt DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 3. Tabel: Moeilijkheden
    # LaatstBewerkt is nu DATETIME
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Moeilijkheden (
        MoeilijkheidsId INTEGER PRIMARY KEY AUTOINCREMENT,
        Moeilijkheid TEXT,
        Snelheid INTEGER,
        GameId INTEGER,
        LaatstBewerkt DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (GameId) REFERENCES Games(GameId)
    );
    """)

    # 4. Tabel: Rondes
    # LaatstBewerkt is nu DATETIME
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Rondes (
        RondeId INTEGER PRIMARY KEY AUTOINCREMENT,
        Nummer INTEGER,
        GameId INTEGER,
        LaatstBewerkt DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (GameId) REFERENCES Games(GameId)
    );
    """)

    # 5. Tabel: Trainings
    # Start is nu DATETIME
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Trainings (
        TrainingsId INTEGER PRIMARY KEY AUTOINCREMENT,
        Start DATETIME DEFAULT CURRENT_TIMESTAMP,
        AantalKleuren INTEGER,
        GebruikersId INTEGER,
        RondeId INTEGER,
        MoeilijkheidsId INTEGER,
        GameId INTEGER,
        FOREIGN KEY (GebruikersId) REFERENCES Gebruikers(GebruikersId),
        FOREIGN KEY (RondeId) REFERENCES Rondes(RondeId),
        FOREIGN KEY (MoeilijkheidsId) REFERENCES Moeilijkheden(MoeilijkheidsId),
        FOREIGN KEY (GameId) REFERENCES Games(GameId)
    );
    """)

    # 6. Tabel: RondeWaarden
    # (Deze heeft volgens het diagram geen datum-kolom)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS RondeWaarden (
        RondeWaardeId INTEGER PRIMARY KEY AUTOINCREMENT,
        TrainingsId INTEGER,
        RondeNummer INTEGER,
        Waarde TEXT,
        Uitkomst TEXT,
        FOREIGN KEY (TrainingsId) REFERENCES Trainings(TrainingsId)
    );
    """)

    print("Database succesvol aangemaakt met DATETIME types!")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_database()