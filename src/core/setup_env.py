import os
import logging
import boto3
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

from rag.rag import (
    fase1_cargar_pdfs_crudos,
    fase2_estructurar_documentos,
    fase3_crear_base_vectorial
)
from data.data_cleaning import fase4_limpiar_csvs

def validar_entorno_nube():
    """Valida que todas las credenciales inyectadas por la plataforma (ej. Coolify) existan."""
    MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
    MINIO_ACCESS = os.getenv("MINIO_ACCESS_KEY") or os.getenv("MINIO_ROOT_USER")
    MINIO_SECRET = os.getenv("MINIO_SECRET_KEY") or os.getenv("MINIO_ROOT_PASSWORD")
    MINIO_BUCKET = os.getenv("MINIO_BUCKET_NAME")

    # 3. Validación de seguridad temprana
    if not MINIO_ENDPOINT or not MINIO_ACCESS or not MINIO_BUCKET:
        raise ValueError("[ERROR] Faltan credenciales de MinIO en las variables de entorno. Verifica la configuración en Dokploy o tu .env")

    # 4. Usar las variables para conectarnos al Data Lake (Prueba rápida)
    endpoint = MINIO_ENDPOINT if MINIO_ENDPOINT.startswith('http') else f"http://{MINIO_ENDPOINT}"
    
    try:
        s3_client = boto3.client(
            's3',
            endpoint_url=endpoint,
            aws_access_key_id=MINIO_ACCESS,
            aws_secret_access_key=MINIO_SECRET
        )
        logger.info("Conexión preparada hacia el bucket en la nube: %s", MINIO_BUCKET)
    except Exception as e:
        raise ValueError(f"[ERROR] Error al inicializar el cliente Boto3 para MinIO: {e}")

class SetupEnvironment:
    @staticmethod
    def inicializar():
        """Configura variables de entorno, índices de FAISS y carga los CSVs."""
        # 1. Cargar entorno local (solo sirve cuando pruebas en tu propia computadora)
        # Cuando el código esté en Coolify, las variables del servidor tendrán prioridad.
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_path = os.path.join(base_dir, '.env')
        load_dotenv(env_path)
        
        logger.info("--- INICIALIZANDO SISTEMA NOVASYNC ---")
        
        # Validar variables de nube antes de empezar procesos pesados
        validar_entorno_nube()
        
        # 1. RAG y Base Vectorial
        docs_crudos = fase1_cargar_pdfs_crudos()
        if docs_crudos:
            docs_procesados = fase2_estructurar_documentos(docs_crudos)
            fase3_crear_base_vectorial(docs_procesados)
            
        # 2. Datos tabulares limpios
        df_client, df_record = fase4_limpiar_csvs()
        return df_client, df_record
