# Usamos la imagen oficial de Python slim (ligera) para evitar consumo excesivo en PaaS
FROM python:3.10-slim

# Evitar que Python escriba archivos .pyc en disco y asegurar que los logs salgan directo a consola
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Definir el directorio donde vivirán los datos persistentes (Volumen en Coolify)
ENV DB_DIR=/app/db

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

# Establecer el directorio de ejecución para que los imports funcionen correctamente
WORKDIR /app/src

# Comando por defecto para ejecutar la aplicación web
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.fileWatcherType=none"]
