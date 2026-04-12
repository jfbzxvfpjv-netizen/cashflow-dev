# ============================================================================
# Dockerfile — Frontend (Vue.js 3 + Nginx)
# ============================================================================
# Build multi-stage:
#   Etapa 1 (build): compila Vue.js 3 con Node.js 20
#   Etapa 2 (serve): sirve los estáticos con Nginx + proxy inverso al backend
# Imágenes base compatibles con ARM64 y x86-64 de forma nativa.
# ============================================================================

# --------------------------------------------------------------------------
# Etapa 1: Build del frontend Vue.js 3
# --------------------------------------------------------------------------
FROM node:20-alpine AS build

WORKDIR /app

# Dependencias (capa cacheada)
COPY frontend/package.json ./
RUN npm install

# Código fuente del frontend
COPY frontend/ .

# Argumento para inyectar el entorno en el build de Vite
ARG ENV=development

# Build de producción
RUN npm run build

# --------------------------------------------------------------------------
# Etapa 2: Nginx como servidor web y proxy inverso
# --------------------------------------------------------------------------
FROM nginx:1.24-alpine

LABEL maintainer="R2iNetwork"
LABEL description="Frontend Gestión Flujo de Caja — Vue.js 3 + Nginx proxy"

# Eliminar configuración por defecto de Nginx
RUN rm -rf /etc/nginx/conf.d/default.conf /usr/share/nginx/html/*

# Copiar los estáticos compilados de Vue.js
COPY --from=build /app/dist /usr/share/nginx/html

# Copiar la configuración de Nginx personalizada
COPY nginx/nginx.conf /etc/nginx/nginx.conf

# Entrypoint que auto-genera certificado autofirmado si no existe
COPY nginx/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Directorio para certificados TLS (montado como volumen o generado por entrypoint)
RUN mkdir -p /etc/nginx/ssl

# Puertos HTTP y HTTPS
EXPOSE 80 443

# Entrypoint genera certs si faltan, luego arranca Nginx
ENTRYPOINT ["/docker-entrypoint.sh"]
