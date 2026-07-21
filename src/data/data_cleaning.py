import pandas as pd
import os
import logging

logger = logging.getLogger(__name__)

def fase4_limpiar_csvs():
    """Carga y limpia los DataFrames leyendo directamente desde MinIO (S3)."""
    df_c, df_r = None, None
    
    endpoint = os.getenv('MINIO_ENDPOINT')
    if endpoint and not endpoint.startswith('http'):
        endpoint = f"http://{endpoint}"
        
    storage_options = {
        "key": os.getenv('MINIO_ACCESS_KEY'),
        "secret": os.getenv('MINIO_SECRET_KEY'),
        "client_kwargs": {
            "endpoint_url": endpoint
        }
    }
    
    bucket_name = os.getenv('MINIO_BUCKET_NAME')
    
    if not bucket_name or not endpoint:
        logger.warning("Variables de entorno de MinIO no configuradas. Omitiendo limpieza de CSVs.")
        return None, None

    client_path = f"s3://{bucket_name}/data/Client.csv"
    record_path = f"s3://{bucket_name}/data/Record.csv"
    
    try:
        df_c = pd.read_csv(client_path, storage_options=storage_options)
        df_c.dropna(how="all", inplace=True)
        df_c.drop_duplicates(inplace=True)
        logger.info("Client.csv procesado desde MinIO. %d registros listos.", len(df_c))
    except Exception as e:
        logger.error("Error cargando Client.csv desde MinIO: %s", e)
        
    try:
        df_r = pd.read_csv(record_path, storage_options=storage_options)
        df_r.dropna(how="all", inplace=True)
        df_r.drop_duplicates(inplace=True)
        # Rellenar NaN en todas las columnas numéricas con 0 (genérico, sin hardcoding)
        numeric_cols = df_r.select_dtypes(include='number').columns
        df_r[numeric_cols] = df_r[numeric_cols].fillna(0)
        logger.info("Record.csv procesado desde MinIO. %d registros listos.", len(df_r))
    except Exception as e:
        logger.error("Error cargando Record.csv desde MinIO: %s", e)

    return df_c, df_r

if __name__ == "__main__":
    print("Ejecutando limpieza de datos...")
    from dotenv import load_dotenv
    load_dotenv()
    fase4_limpiar_csvs()
