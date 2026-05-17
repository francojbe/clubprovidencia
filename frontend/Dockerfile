# Etapa 1: Compilar la aplicación de React
FROM node:20-alpine AS build

WORKDIR /app

# Copiamos archivos de dependencias
COPY package*.json ./
RUN npm install

# Copiamos todo el código fuente
COPY . .

# Argumento para inyectar la URL de la API durante la compilación
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

# Compilamos el proyecto de Vite
RUN npm run build

# Etapa 2: Servir con un servidor web ultra-liviano (Nginx)
FROM nginx:alpine

# Copiamos el resultado de la compilación al directorio web de Nginx
COPY --from=build /app/dist /usr/share/nginx/html

# Exponemos el puerto estándar 80
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
