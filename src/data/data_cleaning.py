import pandas as pd
import os
import logging

logger = logging.getLogger(__name__)

def fase4_limpiar_csvs():
    """Carga y limpia los DataFrames leyendo directamente desde MinIO (S3) usando Boto3."""
    df_c, df_r = None, None
    
    endpoint = os.getenv('MINIO_ENDPOINT')
    if endpoint and not endpoint.startswith('http'):
        endpoint = f"http://{endpoint}"
        
    bucket_name = os.getenv('MINIO_BUCKET_NAME')
    access_key = os.getenv('MINIO_ACCESS_KEY') or os.getenv('MINIO_ROOT_USER')
    secret_key = os.getenv('MINIO_SECRET_KEY') or os.getenv('MINIO_ROOT_PASSWORD')
    
    if not bucket_name or not endpoint or not access_key or not secret_key:
        logger.warning("Variables de entorno de MinIO incompletas. Omitiendo limpieza de CSVs.")
        return None, None

    import boto3
    import io

    try:
        s3 = boto3.client(
            's3',
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
    except Exception as e:
        logger.error("Error al crear cliente S3 con Boto3: %s", e)
        return None, None

    try:
        obj_c = s3.get_object(Bucket=bucket_name, Key="data/Client.csv")
        df_c = pd.read_csv(io.BytesIO(obj_c['Body'].read()))
        df_c.dropna(how="all", inplace=True)
        df_c.drop_duplicates(inplace=True)
        logger.info("Client.csv procesado desde MinIO. %d registros listos.", len(df_c))
    except Exception as e:
        logger.error("Error cargando Client.csv desde MinIO mediante Boto3: %s", e)
        
    try:
        obj_r = s3.get_object(Bucket=bucket_name, Key="data/Record.csv")
        df_r = pd.read_csv(io.BytesIO(obj_r['Body'].read()))
        df_r.dropna(how="all", inplace=True)
        df_r.drop_duplicates(inplace=True)
        # Rellenar NaN en todas las columnas numéricas con 0 (genérico, sin hardcoding)
        numeric_cols = df_r.select_dtypes(include='number').columns
        df_r[numeric_cols] = df_r[numeric_cols].fillna(0)
        logger.info("Record.csv procesado desde MinIO. %d registros listos.", len(df_r))
    except Exception as e:
        logger.error("Error cargando Record.csv desde MinIO mediante Boto3: %s", e)

    return df_c, df_r

if __name__ == "__main__":
    print("Ejecutando limpieza de datos...")
    from dotenv import load_dotenv
    load_dotenv()
    fase4_limpiar_csvs()
