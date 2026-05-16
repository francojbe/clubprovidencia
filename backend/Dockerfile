# Usamos la imagen oficial de Playwright con Python
# Esto garantiza que Chromium y todas sus dependencias de Linux ya estén preinstaladas
FROM mcr.microsoft.com/playwright/python:v1.42.0-jammy

# Directorio de trabajo
WORKDIR /app

# Copiamos el archivo de requerimientos
COPY requirements.txt .

# Instalamos las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código del backend
COPY . .

# Exponemos el puerto de FastAPI
EXPOSE 8000

# Iniciamos el servidor de FastAPI con Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
