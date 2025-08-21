# Guía de uso db_user_config

### Dependencias necesarias para la ejecución de este modulo:

- psycopg2-binary (para la conexión a la base de datos PostgreSQL)
- python-detenv (para acceder a las variables de entorno)

### Variables de entorno criticas

- `DATABASE_URL`: Es la cadena de conexión a la base de datos PostgreSQL.
- `BOT_TOKEN`: token del bot, se almacenara junto al usuario
- `CHAT_ID`: Es el código del chat a donde el bot enviará los mensajes.
- `USER_IDENTIFIER`: Es el identificador (correo) con el cual se respalda y accede a la información de cada usuario en la base de datos.

---

## Esquema de la base de datos

```sql
CREATE TABLE if not EXISTS user_configs(
id SERIAL PRIMARY KEY,
identifier TEXT unique NOT NULL,
bot_token TEXT NOT NULL,
chat_id TEXT NOT NULL
)
```

---

# Funciones principales

1. `get_user_config(identifier)`: Devuelve el BOT_TOKEN y CHAT_ID si existe, None en caso de no existir.
2. `set_user_config(identifier_chat_id)`: Inserta un nuevo usuario usando el BOT_TOKEN de las variables de entorno.
3. `update_user_config(current_identifier, new_identifier, chat_id)`: Actualizar identifier y/o chat_id del usuario.

> Nota:
> Si `DATABASE_URL` no esta configurada en las variables de entorno, lanza una excepcion de tipo ValueError

---

# Ejecución del modulo en la terminal

Una ves configurado en las variables de entorno (.env) DATABASE_URL y BOT_TOKEN.
Desde la raíz del proyecto ejecutar el comando: `python -m utils.db_user_config`

### Opciones en el menú

1. Agregar un nuevo usuario
   1. Pide un identificador (correo) y chat_id.
   2. Inserta el registro junto al BOT_TOKEN del entorno
   3. Mensajes: Registro exitoso, Registro ya existe, error
2. Actualizar usuario existente
   1. Solicita tu identificador actual (current_identifier), un nuevo identificador y chat_id
   2. Valida la existencia del identificador actual y del nuevo también.
   3. Actualizar el identificador y chat_id
3. Consultar configuración de un usuario
   1. Solicita tu identificador
   2. Muestra en pantalla un mensaje de éxito: ✅ Configuración encontrada, en caso contrario muestra un mensaje de advertencia.
4. Salir del programa
   1. Muestra un mensaje

---

## Mensajes y errores comunes

- **“BASE DE DATOS: No fue configurada en variables de entorno.”**
  - Causa: falta DATABASE_URL en .env o entorno.
  - Solución: define DATABASE_URL y reinicia el proceso.
- **“relation user_configs does not exist”**
  - Causa: la tabla no fue creada.
  - Solución: ejecuta el SQL de creación de tabla.
- **“El identificador 'X' ya está en uso.”**
  - Causa: new_identifier duplicado en update_user_config.
  - Solución: elige otro identifier o elimina el existente.
- **“El usuario con identificador 'X' ya existe.”**
  - Causa: set_user_config intenta insertar un identifier ya presente.
  - Solución: usa update_user_config o otro identifier.
- **Falta de dependencias (No module named psycopg2 / dotenv)**
  - Causa: librerías no instaladas.
  - Solución: instala con pip (ver Requisitos).
- **Errores de conexión (timeout, refused)**
  - Causa: credenciales, host, puerto o red.
  - Solución: verifica DATABASE_URL, reachability y reglas de firewall/SSL.

---

## Buenas prácticas y seguridad

- **Protege secretos**
  - Mantén BOT_TOKEN en variables de entorno o gestores de secretos, nunca en repositorio.
- **Múltiples bots**
  - set_user_config inserta el BOT_TOKEN del entorno actual. Si gestionas varios, establece el token adecuado antes de cada inserción o modifica la función para aceptar bot_token como parámetro.
- **Manejo robusto de errores**
  - Para aplicaciones no interactivas, evita depender solo de prints. Considera retornar resultados estructurados o lanzar excepciones específicas.
- **Conexiones a la base**
  - El módulo cierra cursores y conexiones en finally. En escenarios de alto tráfico, evalúa usar pools de conexiones (por ejemplo, psycopg2.pool) y transacciones explícitas.
