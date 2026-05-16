from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import json
from typing import Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os

# Default Mock data
MOCK_CLIENTS = []
MOCK_ATTENDANCE = []

# Try to load from data.json
if os.path.exists('data.json'):
    with open('data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        MOCK_CLIENTS = data.get('clients', [])
        MOCK_ATTENDANCE = data.get('attendance', [])
else:
    MOCK_CLIENTS = [
        {"id": 1, "nombre": "Paulette Salinas", "email": "salinaspaulette@gmail.com", "telefono": "+56 9 1234 5678"},
        {"id": 2, "nombre": "Gab Otavalo", "email": "gabriela.otavalo@gmail.com", "telefono": ""}
    ]
    MOCK_ATTENDANCE = [
        {"n": 4819, "client_id": 1, "nombre": "Paulette Salinas", "clase": "Hidrogimnasia", "horario": "09:15", "fecha": "02-05-2026"}
    ]

class RegistryEntry(BaseModel):
    nombre: str
    email: Optional[str] = ""
    clase: str

class ClientUpdate(BaseModel):
    nombre: str
    email: Optional[str] = ""
    telefono: Optional[str] = ""

@app.get("/users")
def get_users():
    return MOCK_CLIENTS

@app.put("/clients/{client_id}")
def update_client(client_id: int, update: ClientUpdate):
    client = next((u for u in MOCK_CLIENTS if u["id"] == client_id), None)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    client["nombre"] = update.nombre
    client["email"] = update.email
    client["telefono"] = update.telefono
    
    # Update attendance names to keep them in sync
    for a in MOCK_ATTENDANCE:
        if a["client_id"] == client_id:
            a["nombre"] = update.nombre
            
    return {"status": "success", "client": client}

@app.get("/attendance")
def get_all_attendance():
    sorted_attendance = sorted(MOCK_ATTENDANCE, key=lambda x: x["n"], reverse=True)
    return sorted_attendance

@app.post("/register")
def register_entry(entry: RegistryEntry):
    now = datetime.now()
    fecha = now.strftime("%d-%m-%Y")
    horario = now.strftime("%H:%M")
    
    # Check if client exists, else create
    client = next((u for u in MOCK_CLIENTS if u["nombre"].lower() == entry.nombre.lower()), None)
    if not client:
        new_id = max([u["id"] for u in MOCK_CLIENTS]) + 1 if MOCK_CLIENTS else 1
        client = {"id": new_id, "nombre": entry.nombre, "email": entry.email, "telefono": ""}
        MOCK_CLIENTS.append(client)
    
    new_n = max([a["n"] for a in MOCK_ATTENDANCE]) + 1 if MOCK_ATTENDANCE else 1
    
    new_record = {
        "n": new_n,
        "client_id": client["id"],
        "nombre": client["nombre"],
        "clase": entry.clase,
        "horario": horario,
        "fecha": fecha
    }
    MOCK_ATTENDANCE.append(new_record)
    
    return {"status": "success", "message": "Ingreso registrado correctamente", "record": new_record}

@app.get("/clients/{client_id}/history")
def get_client_history(client_id: int):
    history = [a for a in MOCK_ATTENDANCE if a["client_id"] == client_id]
    history.sort(key=lambda x: x["n"], reverse=True)
    return history

import scraper

@app.get("/api/classpass/search")
async def search_classpass_rpa(q: str, time: Optional[str] = None):
    # Triggers the Playwright bot to open the browser, login and search
    try:
        results = await scraper.search_user(q, time)
        return {"status": "success", "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
