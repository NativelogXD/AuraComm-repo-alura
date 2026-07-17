import pandas as pd
import os

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
        print("⚠️ Advertencia: Variables de entorno de MinIO no configuradas. Omitiendo limpieza de CSVs.")
        return None, None

    client_path = f"s3://{bucket_name}/data/Client.csv"
    record_path = f"s3://{bucket_name}/data/Record.csv"
    
    try:
        df_c = pd.read_csv(client_path, storage_options=storage_options)
        df_c.dropna(how="all", inplace=True)
        df_c.drop_duplicates(inplace=True)
        print(f"Client.csv procesado desde MinIO. {len(df_c)} registros listos.")
    except Exception as e:
        print(f"Error cargando Client.csv desde MinIO: {e}")
        
    try:
        df_r = pd.read_csv(record_path, storage_options=storage_options)
        df_r.dropna(how="all", inplace=True)
        df_r.drop_duplicates(inplace=True)
        if 'Latencia' in df_r.columns:
            df_r['Latencia'].fillna(0, inplace=True)
        print(f"Record.csv procesado desde MinIO. {len(df_r)} registros listos.")
    except Exception as e:
        print(f"Error cargando Record.csv desde MinIO: {e}")

    return df_c, df_r

if __name__ == "__main__":
    print("Ejecutando limpieza de datos...")
    from dotenv import load_dotenv
    load_dotenv()
    fase4_limpiar_csvs()
