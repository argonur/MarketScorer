import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

class Database():
    _instance = None

    def __init__(self, connection_factory=None):
        self._connection = None
        self._connection_factory = connection_factory or (lambda: psycopg2.connect(DB_URL, cursor_factory=RealDictCursor))

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._connection = None
        return cls._instance
    
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

    def close(self):
        if self._connection and not self._connection.closed:
            self._connection.close()