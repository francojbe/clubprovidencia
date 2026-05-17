from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import json
import os
from typing import Optional
import database
from timezone_utils import get_chile_time, get_chile_date_str

PERSISTENT_DIR = "/app/data"
if os.path.exists(PERSISTENT_DIR):
    DATA_JSON_PATH = os.path.join(PERSISTENT_DIR, "data.json")
    # Si el volumen persistente está recién montado y vacío, copiamos el data.json original empaquetado en git
    initial_path = os.path.join(os.path.dirname(__file__), "data.json")
    if not os.path.exists(DATA_JSON_PATH) and os.path.exists(initial_path):
        import shutil
        try:
            shutil.copy2(initial_path, DATA_JSON_PATH)
            print("[SISTEMA] Copiado data.json inicial de Git al volumen persistente.")
        except Exception as e:
            print(f"[SISTEMA] Error al inicializar data.json en volumen: {e}")
else:
    DATA_JSON_PATH = os.path.join(os.path.dirname(__file__), "data.json")

# Inicializar Base de Datos SQLite e importar socios del data.json
database.init_db()
database.seed_database_from_json(DATA_JSON_PATH)

app = FastAPI()

import asyncio
import scraper

def is_within_class_hours(dt: datetime) -> bool:
    """
    Verifica si la hora actual está dentro del horario operativo de clases (con 1 hora de margen de seguridad).
    Lunes a Viernes: 07:00 a 21:00 (Ventana de sincronización: 06:00 a 22:00)
    Sábados: 08:00 a 12:30 (Ventana de sincronización: 07:00 a 13:30)
    Domingos: 09:00 a 12:30 (Ventana de sincronización: 08:00 a 13:30)
    """
    wd = dt.weekday()  # 0: Lunes, 6: Domingo
    now_mins = dt.hour * 60 + dt.minute
    
    if wd < 5:  # Lunes a Viernes
        return (6 * 60) <= now_mins <= (22 * 60)
    elif wd == 5:  # Sábado
        return (7 * 60) <= now_mins <= (13 * 60 + 30)
    else:  # Domingo
        return (8 * 60) <= now_mins <= (13 * 60 + 30)

async def classpass_hourly_scheduler():
    """Bucle asíncrono en segundo plano que realiza sincronizaciones automáticas cada 1 hora."""
    # Espera inicial de 10 segundos al levantar el servidor para permitir que se inicie correctamente
    await asyncio.sleep(10)
    while True:
        try:
            now = datetime.now()
            if not is_within_class_hours(now):
                print(f"[SCHEDULER] {now.strftime('%Y-%m-%d %H:%M:%S')} - Fuera del horario de clases. Sincronización automática omitida.")
            else:
                # Si el caché general no está fresco (más de 15 minutos desde el último barrido),
                # realiza el barrido automático de lo que queda de día de forma silenciosa
                if not database.is_cache_fresh(max_age_minutes=15):
                    print("[SCHEDULER] Iniciando sincronización masiva automática...")
                    results = await scraper.sync_all_classes()
                    today_str = now.strftime("%Y-%m-%d")
                    database.save_reservations(results, clear_date=today_str)
                    database.set_last_sync("bulk")
                    print(f"[SCHEDULER] Sincronización automática exitosa. Reservas hoy: {len(results)}")
        except Exception as e:
            print(f"[SCHEDULER] Error en barrido automático de ClassPass: {e}")
        
        # Esperar 1 hora (3600 segundos) para la siguiente validación
        await asyncio.sleep(3600)

@app.on_event("startup")
async def startup_event():
    print("[SISTEMA] ¡Servidor backend iniciado exitosamente!")
    print("[SISTEMA] Inicializando base de datos SQLite para caché local...")
    print("[SISTEMA] Iniciando el planificador automático de ClassPass (revisión cada 1 hora en hora Chile)...")
    # Inicia el planificador en segundo plano sin interrumpir el arranque normal de FastAPI
    asyncio.create_task(classpass_hourly_scheduler())

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RegistryEntry(BaseModel):
    nombre: str
    email: Optional[str] = ""
    clase: str

class ClientUpdate(BaseModel):
    nombre: str
    email: Optional[str] = ""
    telefono: Optional[str] = ""

class ClientCreate(BaseModel):
    nombre: str
    email: Optional[str] = ""
    telefono: Optional[str] = ""

@app.post("/clients")
def add_new_client(client: ClientCreate):
    existing = database.get_client_by_name(client.nombre)
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe un socio con este nombre")
    client_id = database.create_client(client.nombre, client.email or "", client.telefono or "")
    new_client = database.get_client_by_id(client_id)
    return {"status": "success", "client": new_client}

@app.get("/users")
def get_users():
    return database.get_all_clients()

@app.put("/clients/{client_id}")
def update_client(client_id: int, update: ClientUpdate):
    client = database.get_client_by_id(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Socio no encontrado")
    
    database.update_client_in_db(client_id, update.nombre, update.email or "", update.telefono or "")
    updated_client = database.get_client_by_id(client_id)
    return {"status": "success", "client": updated_client}

@app.get("/attendance")
def get_all_attendance():
    return database.get_all_attendance_records()

@app.post("/register")
def register_entry(entry: RegistryEntry):
    now = get_chile_time()
    fecha = now.strftime("%d-%m-%Y")
    horario = now.strftime("%H:%M")
    
    # Buscar o crear socio en la base de datos
    client = database.get_client_by_name(entry.nombre)
    if not client:
        client_id = database.create_client(entry.nombre, entry.email or "", "")
        client = database.get_client_by_id(client_id)
    else:
        client_id = client["id"]
        # Si no tenía correo y ahora lo provee, lo agregamos automáticamente
        if entry.email and not client["email"]:
            database.update_client_in_db(client_id, client["nombre"], entry.email, client["telefono"] or "")
            client["email"] = entry.email
            
    # Registrar la asistencia en SQLite
    record_id = database.register_attendance_in_db(client_id, client["nombre"], entry.clase, horario, fecha)
    
    new_record = {
        "n": record_id,
        "client_id": client_id,
        "nombre": client["nombre"],
        "clase": entry.clase,
        "horario": horario,
        "fecha": fecha
    }
    return {"status": "success", "message": "Ingreso registrado correctamente", "record": new_record}

@app.get("/clients/{client_id}/history")
def get_client_history(client_id: int):
    return database.get_client_attendance_history(client_id)

import scraper

@app.get("/api/classpass/status")
def get_classpass_cache_status():
    last_sync = database.get_last_sync("bulk")
    fresh = database.is_cache_fresh(max_age_minutes=15)
    return {
        "last_sync": last_sync.isoformat() if last_sync else None,
        "is_fresh": fresh,
        "max_age_minutes": 15
    }

@app.post("/api/classpass/sync")
async def sync_classpass_database():
    try:
        # 1. Ejecutar raspado masivo diario
        results = await scraper.sync_all_classes()
        
        # 2. Guardar en la DB (limpiamos registros de hoy primero para evitar duplicados)
        today_str = get_chile_date_str()
        database.save_reservations(results, clear_date=today_str)
        
        # 3. Registrar metadata de sincronización
        database.set_last_sync("bulk")
        
        return {
            "status": "success", 
            "message": f"Sincronización masiva completada con éxito. Se importaron {len(results)} reservas hoy.",
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/classpass/search")
async def search_classpass_rpa(q: str, time: Optional[str] = None):
    try:
        # 1. Buscar SIEMPRE primero en la base de datos local (Independiente del tiempo transcurrido)
        # Si el alumno ya fue mapeado hoy, responderemos en 1ms, evitando encender el bot innecesariamente.
        cached_data = database.query_cache_user(q)
        if cached_data:
            return {
                "status": "success", 
                "source": "cache",
                "data": cached_data
            }
        
        # 2. Si no está en la DB, pero el caché masivo se hizo hace menos de 15 minutos,
        # podemos dar por seguro que no está inscrito hoy (sin tener que encender el bot).
        if database.is_cache_fresh(max_age_minutes=15):
            return {
                "status": "success", 
                "source": "cache",
                "data": []
            }
        
        # 3. Solo si NO está en la DB y el caché general está expirado, cae de respaldo al bot RPA en vivo
        results = await scraper.search_user(q, time)
        
        # 4. Si el bot en vivo encuentra al usuario, lo guardamos en caché de inmediato
        if results:
            today_str = get_chile_date_str()
            db_entries = []
            for r in results:
                for c in r.get("classes", []):
                    db_entries.append({
                        "user_name": r["nombre"],
                        "class_name": c["clase"],
                        "class_time": c["horario"],
                        "class_date": today_str
                    })
            database.save_reservations(db_entries)
            
        return {
            "status": "success", 
            "source": "live",
            "data": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
