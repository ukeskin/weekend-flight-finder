# Stage 1: Build frontend
FROM node:20-alpine AS frontend-build
WORKDIR /app
COPY frontend/package.json ./
RUN npm install
COPY frontend/ .
ARG VITE_API_KEY
ARG VITE_API_BASE=""
ENV VITE_API_KEY=$VITE_API_KEY
ENV VITE_API_BASE=$VITE_API_BASE
RUN npm run build

# Stage 2: Backend + Nginx
FROM python:3.12-slim

RUN apt-get update && apt-get install -y nginx supervisor && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python deps
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Backend code
COPY backend/ ./backend/
COPY data_processing.py .

# SQLite database (compressed)
COPY data/flights.db.gz ./data/
RUN gunzip ./data/flights.db.gz

# Frontend built files
COPY --from=frontend-build /app/dist /usr/share/nginx/html

# Nginx config
RUN rm /etc/nginx/sites-enabled/default
COPY deploy/nginx-site.conf /etc/nginx/sites-enabled/default

# Supervisor config
COPY deploy/supervisord.conf /etc/supervisor/conf.d/app.conf

EXPOSE 80

CMD ["supervisord", "-n", "-c", "/etc/supervisor/conf.d/app.conf"]
