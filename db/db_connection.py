import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

class Database:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            # Creamos la única instancia
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._connection = None
        return cls._instance

    def __init__(self, connection_factory=None):
        # Sólo sobreescribimos el factory si lo pasaron
        if connection_factory is not None:
            self._connection_factory = connection_factory
        else:
            # En el primer init define el factory por defecto
            self._connection_factory = getattr(
                self, "_connection_factory",
                lambda: psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
            )
    
    # Metodo que permite reiniciar el singleton (Util para los tests)
    @classmethod
    def _reset_instance(cls):
        cls._instance = None
    
    def connect(self):
        if self._connection is None or self._connection.closed:
            try:
                self._connection = self._connection_factory()
            except Exception as e:
                raise Exception(f"Error al conectar a la base de datos: {e}")
    
    def get_connection(self):
        if self._connection is None or self._connection.closed:
            self.connect()
        return self._connection
    
    def execute_query(self, query, params=None):
        conn = self.get_connection()
        with conn.cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchall()
        
    def execute_non_query(self, query, params=None):
        conn = self.get_connection()
        with conn.cursor() as cursor:
            cursor.execute(query, params or ())
            conn.commit()
            return cursor.rowcount

    def close(self):
        if self._connection and not self._connection.closed:
            self._connection.close()