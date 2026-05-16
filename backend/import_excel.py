import pandas as pd
import json
import math

def import_excel():
    excel_path = r'C:\Users\franc\OneDrive\Documentos\dev\Analisis de asitencia\Accesos ClassPass .xlsx'
    
    # Read Excel file
    try:
        df = pd.read_excel(excel_path)
    except Exception as e:
        print(f"Error reading Excel: {e}")
        return

    # Assuming columns are like: N°, NOMBRE, MAIL, CLASE, HORARIO, FECHA
    # We will try to map them dynamically if they have slightly different names
    
    # Standardize column names
    col_mapping = {}
    for col in df.columns:
        clean_col = str(col).strip().upper()
        if 'N°' in clean_col or 'NRO' in clean_col: col_mapping[col] = 'n'
        elif 'NOMBRE' in clean_col: col_mapping[col] = 'nombre'
        elif 'MAIL' in clean_col or 'CORREO' in clean_col: col_mapping[col] = 'email'
        elif 'CLASE' in clean_col or 'ACTIVIDAD' in clean_col: col_mapping[col] = 'clase'
        elif 'HORA' in clean_col: col_mapping[col] = 'horario'
        elif 'FECHA' in clean_col: col_mapping[col] = 'fecha'
    
    df = df.rename(columns=col_mapping)
    
    # Drop rows without names
    if 'nombre' in df.columns:
        df = df.dropna(subset=['nombre'])
    
    clients = []
    attendance = []
    
    # Helper to clean strings and handle NaNs
    def clean_val(val):
        if pd.isna(val): return ""
        return str(val).strip()
    
    client_map = {} # name lower -> client dict
    client_id_counter = 1
    
    for idx, row in df.iterrows():
        nombre = clean_val(row.get('nombre', ''))
        if not nombre: continue
        
        email = clean_val(row.get('email', ''))
        
        n_val = row.get('n', 0)
        try:
            n = int(n_val)
        except:
            n = idx + 1
            
        clase = clean_val(row.get('clase', ''))
        horario = clean_val(row.get('horario', ''))
        fecha = clean_val(row.get('fecha', ''))
        
        # If fecha is a datetime object, format it
        if isinstance(row.get('fecha'), pd.Timestamp):
            fecha = row['fecha'].strftime('%d-%m-%Y')
            
        # Manage unique clients
        name_key = nombre.lower()
        if name_key not in client_map:
            client_map[name_key] = {
                "id": client_id_counter,
                "nombre": nombre,
                "email": email,
                "telefono": ""
            }
            client_id_counter += 1
            
        # If client existed but we found an email now, update it
        if email and not client_map[name_key]["email"]:
            client_map[name_key]["email"] = email
            
        client_id = client_map[name_key]["id"]
        
        # Add to attendance
        attendance.append({
            "n": n,
            "client_id": client_id,
            "nombre": nombre,
            "clase": clase,
            "horario": horario,
            "fecha": fecha
        })
        
    data = {
        "clients": list(client_map.values()),
        "attendance": attendance
    }
    
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully exported {len(data['clients'])} clients and {len(data['attendance'])} attendance records to data.json")

if __name__ == "__main__":
    import_excel()
