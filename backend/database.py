import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")

def init_db():
    """Inicializa las tablas de SQLite si no existen."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabla para almacenar las reservas de ClassPass extraídas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS classpass_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT NOT NULL,
            class_name TEXT NOT NULL,
            class_time TEXT NOT NULL,
            class_date TEXT NOT NULL, -- Formato: YYYY-MM-DD
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    now_str = datetime.now().isoformat()
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
        return datetime.fromisoformat(row[0])
    return None

def is_cache_fresh(max_age_minutes=15):
    """Determina si se hizo una sincronización masiva recientemente hoy."""
    last_sync = get_last_sync("bulk")
    if not last_sync:
        return False
        
    # Verificar si es el mismo día y si la diferencia es menor que max_age_minutes
    now = datetime.now()
    if last_sync.date() != now.date():
        return False
        
    diff = now - last_sync
    diff_minutes = diff.total_seconds() / 60.0
    return diff_minutes < max_age_minutes

def query_cache_user(search_query):
    """Busca en el caché local a un usuario usando comparación normalizada de SQLite."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    
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
