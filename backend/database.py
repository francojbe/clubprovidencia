import sqlite3
import os
from datetime import datetime
from timezone_utils import get_chile_time, get_chile_date_str, CHILE_TZ

PERSISTENT_DIR = "/app/data"
if os.path.exists(PERSISTENT_DIR):
    DB_PATH = os.path.join(PERSISTENT_DIR, "database.db")
else:
    DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")

def init_db():
    """Inicializa las tablas de SQLite si no existen."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabla para almacenar las reservas de ClassPass extraídas con constraint UNIQUE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS classpass_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT NOT NULL,
            class_name TEXT NOT NULL,
            class_time TEXT NOT NULL,
            class_date TEXT NOT NULL, -- Formato: YYYY-MM-DD
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_name, class_name, class_time, class_date)
        )
    """)
    
    # Tabla de metadatos para guardar el estado y hora del último barrido masivo completo
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sync_meta (
            key TEXT PRIMARY KEY,
            val TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Nueva Tabla para los Socios del Directorio
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            email TEXT,
            telefono TEXT
        )
    """)
    
    # Nueva Tabla para el Historial de Asistencias (Check-in)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            nombre TEXT NOT NULL,
            clase TEXT NOT NULL,
            horario TEXT NOT NULL,
            fecha TEXT NOT NULL, -- Formato: DD-MM-YYYY
            FOREIGN KEY(client_id) REFERENCES clients(id)
        )
    """)
    
    # Limpieza automática preventiva de cualquier duplicado preexistente en la base de datos
    cursor.execute("""
        DELETE FROM classpass_cache
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM classpass_cache
            GROUP BY user_name, class_name, class_time, class_date
        )
    """)
    
    conn.commit()
    conn.close()

def save_reservations(reservations, clear_date=None):
    """
    Guarda una lista de reservas en el caché.
    Si se provee `clear_date` (formato YYYY-MM-DD), elimina primero las reservas de esa fecha
    para evitar duplicados antes de insertar.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if clear_date:
        cursor.execute("DELETE FROM classpass_cache WHERE class_date = ?", (clear_date,))
        
    for res in reservations:
        # Prevenir duplicados de manera robusta y compatible con bases de datos existentes
        cursor.execute("""
            SELECT 1 FROM classpass_cache 
            WHERE user_name = ? AND class_name = ? AND class_time = ? AND class_date = ?
        """, (res["user_name"], res["class_name"], res["class_time"], res["class_date"]))
        if cursor.fetchone():
            continue  # Si ya existe exactamente igual, saltar inserción
            
        cursor.execute("""
            INSERT INTO classpass_cache (user_name, class_name, class_time, class_date, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (res["user_name"], res["class_name"], res["class_time"], res["class_date"]))
        
    conn.commit()
    conn.close()

def set_last_sync(sync_type="bulk"):
    """Registra la marca de tiempo del último barrido."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now_str = get_chile_time().isoformat()
    cursor.execute("""
        INSERT INTO sync_meta (key, val, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(key) DO UPDATE SET val = excluded.val, updated_at = CURRENT_TIMESTAMP
    """, (sync_type, now_str))
    conn.commit()
    conn.close()

def get_last_sync(sync_type="bulk"):
    """Obtiene la fecha/hora del último barrido."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT val FROM sync_meta WHERE key = ?", (sync_type,))
    row = cursor.fetchone()
    conn.close()
    if row:
        dt = datetime.fromisoformat(row[0])
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=CHILE_TZ)
        return dt
    return None

def is_cache_fresh(max_age_minutes=15):
    """Determina si se hizo una sincronización masiva recientemente hoy."""
    last_sync = get_last_sync("bulk")
    if not last_sync:
        return False
        
    # Verificar si es el mismo día y si la diferencia es menor que max_age_minutes
    now = get_chile_time()
    if last_sync.date() != now.date():
        return False
        
    diff = now - last_sync
    diff_minutes = diff.total_seconds() / 60.0
    return diff_minutes < max_age_minutes

def query_cache_user(search_query):
    """Busca en el caché local a un usuario usando comparación normalizada de SQLite."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    today_str = get_chile_date_str()
    
    # Traemos todos los registros de hoy para filtrarlos/normalizarlos en Python
    # Esto es mucho más seguro para match difusos en SQLite
    cursor.execute("SELECT user_name, class_name, class_time FROM classpass_cache WHERE class_date = ?", (today_str,))
    rows = cursor.fetchall()
    conn.close()
    
    def normalize(text):
        if not text: return ""
        import unicodedata
        t = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8')
        return t.lower().strip()
        
    q_norm = normalize(search_query)
    results = []
    matched_name = ""
    
    for row in rows:
        db_user = row[0]
        db_class = row[1]
        db_time = row[2]
        
        if q_norm in normalize(db_user):
            matched_name = db_user
            results.append({
                "clase": db_class,
                "horario": db_time,
                "fecha": "Hoy (Caché local)"
            })
            
    if results:
        return [{
            "id": 9999,
            "nombre": matched_name,
            "email": "classpass@live.com",
            "classes": results
        }]
    return []

def get_all_clients():
    """Retorna todos los socios del directorio ordenados por nombre."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, email, telefono FROM clients ORDER BY nombre ASC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_client_by_name(name):
    """Busca un socio por su nombre (insensible a mayúsculas)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, email, telefono FROM clients WHERE LOWER(nombre) = LOWER(?)", (name.strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_client_by_id(client_id):
    """Busca un socio por su ID único."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, email, telefono FROM clients WHERE id = ?", (client_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def create_client(nombre, email="", telefono=""):
    """Crea un nuevo socio en el directorio y retorna su ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO clients (nombre, email, telefono) VALUES (?, ?, ?)", (nombre.strip(), email.strip(), telefono.strip()))
        client_id = cursor.lastrowid
        conn.commit()
    except sqlite3.IntegrityError:
        cursor.execute("SELECT id FROM clients WHERE LOWER(nombre) = LOWER(?)", (nombre.strip(),))
        row = cursor.fetchone()
        client_id = row[0] if row else None
    conn.close()
    return client_id

def update_client_in_db(client_id, nombre, email, telefono):
    """Actualiza la información de un socio e impacta su nombre en asistencias."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE clients 
        SET nombre = ?, email = ?, telefono = ? 
        WHERE id = ?
    """, (nombre.strip(), email.strip(), telefono.strip(), client_id))
    cursor.execute("""
        UPDATE attendance 
        SET nombre = ? 
        WHERE client_id = ?
    """, (nombre.strip(), client_id))
    conn.commit()
    conn.close()

def get_all_attendance_records():
    """Retorna todo el historial de check-ins en orden descendente."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id as n, client_id, nombre, clase, horario, fecha FROM attendance ORDER BY id DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_client_attendance_history(client_id):
    """Retorna el historial de check-ins para un socio específico."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id as n, client_id, nombre, clase, horario, fecha FROM attendance WHERE client_id = ? ORDER BY id DESC", (client_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def register_attendance_in_db(client_id, nombre, clase, horario, fecha):
    """Registra una asistencia manual en la base de datos."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO attendance (client_id, nombre, clase, horario, fecha)
        VALUES (?, ?, ?, ?, ?)
    """, (client_id, nombre.strip(), clase.strip(), horario.strip(), fecha.strip()))
    record_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return record_id

def seed_database_from_json(json_path):
    """Importa los socios e historial desde data.json a SQLite si la tabla de socios está vacía."""
    if not os.path.exists(json_path):
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Comprobar si ya existen socios
    cursor.execute("SELECT COUNT(id) FROM clients")
    count = cursor.fetchone()[0]
    if count > 0:
        conn.close()
        return # Ya hay datos
        
    print(f"[SISTEMA] Sembrando directorio y asistencias desde {json_path} hacia SQLite...")
    import json
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        clients_data = data.get('clients', [])
        attendance_data = data.get('attendance', [])
        
        id_mapping = {}
        
        # Insertar socios
        for c in clients_data:
            cursor.execute("""
                INSERT OR IGNORE INTO clients (nombre, email, telefono) 
                VALUES (?, ?, ?)
            """, (c["nombre"].strip(), c.get("email", "").strip(), c.get("telefono", "").strip()))
            
            # Obtener el ID asignado
            cursor.execute("SELECT id FROM clients WHERE nombre = ?", (c["nombre"].strip(),))
            db_id = cursor.fetchone()[0]
            id_mapping[c["id"]] = db_id
            
        # Insertar asistencias
        for a in attendance_data:
            old_client_id = a.get("client_id")
            new_client_id = id_mapping.get(old_client_id, None)
            cursor.execute("""
                INSERT INTO attendance (client_id, nombre, clase, horario, fecha) 
                VALUES (?, ?, ?, ?, ?)
            """, (new_client_id, a["nombre"].strip(), a["clase"].strip(), a["horario"].strip(), a["fecha"].strip()))
            
        conn.commit()
        print(f"[SISTEMA] Migración exitosa de {len(clients_data)} socios y {len(attendance_data)} asistencias a SQLite.")
    except Exception as e:
        print(f"[ERROR] No se pudo sembrar SQLite desde data.json: {e}")
    finally:
        conn.close()
