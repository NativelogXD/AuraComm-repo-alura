# Usamos la imagen oficial de Python slim (ligera) para evitar consumo excesivo en PaaS
FROM python:3.11-slim

# Evitar que Python escriba archivos .pyc en disco y asegurar que los logs salgan directo a consola
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Definir el directorio donde vivirán los datos persistentes (Volumen en Dokploy)
ENV DB_DIR=/app/db

# Instalar curl para el HEALTHCHECK
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Crear el directorio de trabajo
WORKDIR /app

# Primero copiar solo el requirements.txt para aprovechar el caché de Docker
# si las dependencias no cambian.
COPY src/requirements.txt /app/src/requirements.txt

# Instalar dependencias con la flag --no-cache-dir para mantener la imagen pequeña
RUN pip install --no-cache-dir -r /app/src/requirements.txt

# Copiar el resto del código fuente
COPY src/ /app/src/

# Crear la carpeta de base de datos dentro de la imagen por defecto
RUN mkdir -p /app/db

# Establecer el directorio de ejecución para que los imports funcionen correctamente y coincida con local
WORKDIR /app

# Copiar la configuración global de Streamlit
COPY .streamlit/ /app/.streamlit/

# Healthcheck para que Dokploy sepa si la app está viva
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Comando por defecto para ejecutar la aplicación web
CMD ["streamlit", "run", "src/main.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.fileWatcherType=none"]
