import sqlite3
import os
from backend.config import DATABASE_PATH  # pip install mysql-connector-python niet meer nodig

class Database:

    @staticmethod
    def __open_connection():
        try:
            db = sqlite3.connect(DATABASE_PATH, timeout=30)
            db.row_factory = sqlite3.Row  # Voor dict-achtige resultaten
            cursor = db.cursor()
            return db, cursor
        except sqlite3.Error as err:
            print(f"Database connectie fout: {err}")
            return None, None

    # Executes READS - retourneert lijst van dicts
    @staticmethod
    def get_rows(sqlQuery, params=None):
        db, cursor = Database.__open_connection()
        if not db:
            return None
        try:
            cursor.execute(sqlQuery, params or ())
            rows = cursor.fetchall()
            result = [dict(row) for row in rows]  # Naar echte dicts
            cursor.close()
            db.close()
            return result
        except Exception as error:
            print(f"Query fout: {error}")
            cursor.close()
            db.close()
            return None

    @staticmethod
    def get_one_row(sqlQuery, params=None):
        db, cursor = Database.__open_connection()
        if not db:
            return None
        try:
            cursor.execute(sqlQuery, params or ())
            row = cursor.fetchone()
            cursor.close()
            db.close()
            if row is None:
                raise ValueError("Geen resultaat gevonden.[DB Error]")
            return dict(row)
        except Exception as error:
            print(f"Query fout: {error}")
            cursor.close()
            db.close()
            return None

    # Executes INSERT, UPDATE, DELETE
    @staticmethod
    def execute_sql(sqlQuery, params=None):
        db, cursor = Database.__open_connection()
        if not db:
            return None
        try:
            cursor.execute(sqlQuery, params or ())
            db.commit()
            
            last_id = cursor.lastrowid
            if last_id is not None and last_id > 0:
                result = last_id  # INSERT
            else:
                result = cursor.rowcount  # UPDATE/DELETE
                
            if result == -1:
                raise Exception("Fout in SQL")
            elif result == 0:
                result = 0  # Niets gewijzigd
                
        except sqlite3.Error as error:
            db.rollback()
            result = None
            print(f"SQL fout: Data niet opgeslagen. {error}")
        finally:
            cursor.close()
            db.close()
            return result