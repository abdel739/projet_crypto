import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


class DatabaseManager:
    def __init__(self):
        # Configuration via variables d'environnement
        self.config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'crypto_final'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', ''),
            'port': os.getenv('DB_PORT', '5432')
        }

    def execute_action(self, query, params=None):
        """
        Pour les operations d'ecriture : INSERT, UPDATE, DELETE.
        Retourne True si reussi, False sinon.
        """
        try:
            with psycopg2.connect(**self.config) as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    conn.commit()
                    return True
        except Exception as e:
            print(f"Erreur SQL (Action) : {e}")
            return False

    def execute_query(self, query, params=None):
        """
        Pour les operations de lecture : SELECT.
        Retourne une liste de resultats (tuples).
        """
        try:
            with psycopg2.connect(**self.config) as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    return cur.fetchall()
        except Exception as e:
            print(f"Erreur SQL (Query) : {e}")
            return []

    def tester_connexion(self):
        """Petite fonction utilitaire pour verifier que tout est OK."""
        if self.execute_query("SELECT 1;"):
            print("Connexion a PostgreSQL reussie !")
            return True
        return False


if __name__ == "__main__":
    db = DatabaseManager()
    db.tester_connexion()
