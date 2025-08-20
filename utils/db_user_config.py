import os
import psycopg2
from psycopg2.extras import DictCursor
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")
BOT_TOKEN = os.getenv("BOT_TOKEN")

def get_user_config(identifier: str) -> dict | None:
    if not DB_URL:
        raise ValueError("BASE DE DATOS: No fue configurada en variables de entorno.")
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(DB_URL, cursor_factory=DictCursor)
        cur = conn.cursor()
        query = (
            "SELECT bot_token, chat_id "
            "FROM user_configs "
            "WHERE identifier = %s"
        )
        cur.execute(query, (identifier,))
        row = cur.fetchone()
        if row:
            return {"BOT_TOKEN": row["bot_token"], "CHAT_ID": row["chat_id"]}
        return None
    except Exception as e:
        print(f"[DB Error] No se pudo obtener configuración: {e}")
        return None
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def set_user_config(identifier: str, chat_id: str):
    if not DB_URL:
        raise ValueError("BASE DE DATOS: No fue configurada en variables de entorno.")
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(DB_URL, cursor_factory=DictCursor)
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM user_configs WHERE identifier = %s", (identifier,))
        if cur.fetchone():
            print(f"⚠️ El usuario con identificador '{identifier}' ya existe.")
            return
        query = (
            "INSERT INTO user_configs (identifier, bot_token, chat_id) "
            "VALUES (%s, %s, %s)"
        )
        cur.execute(query, (identifier, BOT_TOKEN, chat_id))
        conn.commit()
        print("✅ Usuario agregado exitosamente.")
    except Exception as e:
        print(f"❌ Error al insertar usuario: {e}")
        return None
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def update_user_config(current_identifier: str, new_identifier: str, chat_id: str):
    if not DB_URL:
        raise ValueError("BASE DE DATOS: No fue configurada en variables de entorno.")
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(DB_URL, cursor_factory=DictCursor)
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM user_configs WHERE identifier = %s", (current_identifier,))
        if not cur.fetchone():
            print(f"⚠️ El usuario '{current_identifier}' no existe.")
            return
        if new_identifier != current_identifier:
            cur.execute("SELECT 1 FROM user_configs WHERE identifier = %s", (new_identifier,))
            if cur.fetchone():
                print(f"⚠️ El identificador '{new_identifier}' ya está en uso.")
                return
        query = (
            "UPDATE user_configs "
            "SET identifier = %s, chat_id = %s "
            "WHERE identifier = %s"
        )
        cur.execute(query, (new_identifier, chat_id, current_identifier))
        conn.commit()
        print("✅ Usuario actualizado exitosamente.")
    except Exception as e:
        print(f"❌ Error al actualizar usuario: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

###### Main con Menú interactivo #####
if __name__ == "__main__": # pragma: no cover
    while True:
        print("\n=== Menú de Configuración del BOT ===")
        print("1. Agregar nuevo usuario")
        print("2. Actualizar usuario existente")
        print("3. Consultar configuración de un usuario")
        print("4. Salir")
        opcion = input("Seleccione una opción: ").strip()

        if opcion == '1':
            identifier = input("Ingrese su identificador (correo): ").strip()
            chat_id = input("Ingrese su CHAT_ID: ").strip()

            if identifier and chat_id:
                set_user_config(identifier, chat_id)
            else:
                print("⚠️ Datos inválidos.")
        elif opcion == '2':
            current_identifier = input("Ingrese su identidicador actual: ").strip()
            new_identifier = input("Ingrese su nuevo identificador (correo): ").strip()
            chat_id = input("Ingrese nuevo chat_id").strip()

            if current_identifier and new_identifier and chat_id:
                update_user_config(current_identifier, new_identifier, chat_id)
            else:
                print("⚠️ Datos inválidos.")

        elif opcion == '3':
            identifier = input("Ingrese su identificador: ").strip()
            config = get_user_config(identifier)

            if config:
                print(f"✅ Configuración encontrada: {config}")
            else:
                print("⚠️ Usuario no encontrado.")
        elif opcion == '4':
            print("👋 Saliendo del programa.")
            break
        else:
            print("⚠️ Opción inválida. Intente nuevamente.")