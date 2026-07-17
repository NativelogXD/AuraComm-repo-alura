import os
import sys
import pandas as pd
from dotenv import load_dotenv

# Añadimos la carpeta padre (src) al path para que encuentre el .env si hace falta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()  # Asume que el .env está en src/

endpoint = os.getenv('MINIO_ENDPOINT')
if endpoint and not endpoint.startswith('http'):
    endpoint = f"http://{endpoint}"

print("--- INICIANDO PRUEBAS DE CONEXIÓN A MINIO ---")
print(f"Endpoint configurado: {endpoint}")
print(f"Bucket configurado: {os.getenv('MINIO_BUCKET_NAME')}\n")

def probar_conexion_pandas():
    print("[1] Probando lectura de DataFrame (CSV) directo desde MinIO...")
    try:
        storage_options = {
            "key": os.getenv('MINIO_ACCESS_KEY'),
            "secret": os.getenv('MINIO_SECRET_KEY'),
            "client_kwargs": {
                "endpoint_url": endpoint
            }
        }
        bucket_name = os.getenv('MINIO_BUCKET_NAME')
        archivo_csv = "data/Client.csv" 
        
        ruta_s3 = f"s3://{bucket_name}/{archivo_csv}"
        
        print(f"-> Intentando leer: {ruta_s3}")
        df = pd.read_csv(ruta_s3, storage_options=storage_options)
        print(f"[EXITO] Se leyeron {len(df)} registros. Mostrando el head():")
        print(df.head())
        print("-" * 50)
        return True
    except Exception as e:
        print(f"[ERROR] leyendo CSV desde MinIO: {e}")
        print("-" * 50)
        return False

def probar_conexion_langchain():
    print("\n[2] Probando S3DirectoryLoader (PDFs) directo desde MinIO...")
    try:
        from langchain_community.document_loaders import S3DirectoryLoader
        
        loader = S3DirectoryLoader(
            bucket=os.getenv('MINIO_BUCKET_NAME'),
            endpoint_url=endpoint,
            aws_access_key_id=os.getenv('MINIO_ACCESS_KEY'),
            aws_secret_access_key=os.getenv('MINIO_SECRET_KEY'),
            prefix="data/" 
        )
        
        print(f"-> Conectando al bucket '{os.getenv('MINIO_BUCKET_NAME')}' para descargar documentos...")
        documentos = loader.load()
        print(f"[EXITO] Se cargaron {len(documentos)} documentos (páginas).")
        if len(documentos) > 0:
             print(f"Muestra del doc 1: {documentos[0].metadata['source']}")
        print("-" * 50)
        return True
    except Exception as e:
        print(f"[ERROR] usando S3DirectoryLoader: {e}")
        print("-" * 50)
        return False

if __name__ == "__main__":
    if not os.getenv('MINIO_ENDPOINT') or not os.getenv('MINIO_ACCESS_KEY'):
         print("[ERROR]: No se encontraron las variables de entorno de MINIO en tu archivo .env.")
         print("Asegúrate de configurar MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY y MINIO_BUCKET_NAME.")
         sys.exit(1)
         
    exito_csv = probar_conexion_pandas()
    exito_pdf = probar_conexion_langchain()
    
    if exito_csv and exito_pdf:
        print("\n[OK] ¡TODAS LAS PRUEBAS PASARON! El sistema puede leer de MinIO sin problemas.")
        print("Ya podemos proceder con la Fase 2 del plan (Refactorización de la app).")
    else:
        print("\n[ADVERTENCIA] ALGUNAS PRUEBAS FALLARON. Revisa tus credenciales o los nombres de los archivos en tu bucket.")
