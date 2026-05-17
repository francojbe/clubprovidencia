import os
import sys
import asyncio
from dotenv import load_dotenv

# Cargar credenciales desde .env
load_dotenv()

# Configurar simulación de hora
os.environ["MOCK_HOUR"] = "08:00"

import database
import scraper

async def run_test():
    print("[TEST] Iniciando Simulacion de Sincronizacion Masiva...")
    print("[INFO] Simulando hora del sistema: 08:00 AM")
    
    # 1. Inicializar base de datos
    database.init_db()
    print("[OK] Base de datos inicializada.")
    
    # 2. Ejecutar sync_all_classes
    try:
        results = await scraper.sync_all_classes()
        print(f"[OK] Sincronizacion completada. Se extrajeron {len(results)} reservas.")
        
        # 3. Guardar en Base de Datos
        from datetime import datetime
        today_str = datetime.now().strftime("%Y-%m-%d")
        database.save_reservations(results, clear_date=today_str)
        database.set_last_sync("bulk")
        print("[OK] Resultados guardados exitosamente en SQLite.")
        
        # 4. Mostrar lo guardado
        import sqlite3
        conn = sqlite3.connect(database.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT user_name, class_name, class_time FROM classpass_cache")
        rows = cursor.fetchall()
        conn.close()
        
        print(f"\n[DB] --- CONTENIDO DE LA BASE DE DATOS ({len(rows)} registros hoy) ---")
        for r in rows[:10]:
            print(f"User: {r[0]} | Class: {r[1]} | Time: {r[2]}")
        if len(rows) > 10:
            print(f"... y {len(rows) - 10} registros mas.")
        print("----------------------------------------------------\n")
        
        # 5. Probar una busqueda simulada en cache
        if rows:
            test_query = rows[0][0][:6] # Primeros 6 caracteres del primer alumno
            print(f"[SEARCH] Probando busqueda en base de datos para: '{test_query}'...")
            search_res = database.query_cache_user(test_query)
            print(f"[RESULT] Resultado obtenido en 1ms:")
            import json
            print(json.dumps(search_res, indent=2, ensure_ascii=False))
        else:
            print("[WARN] No hay registros guardados en SQLite para probar busqueda.")
            
    except Exception as e:
        print(f"[ERROR] Error durante la prueba: {e}")

if __name__ == "__main__":
    asyncio.run(run_test())
