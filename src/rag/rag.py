import os
import logging
import hashlib
import shutil
import boto3
from botocore.exceptions import ClientError
import io
import pypdf
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import re
from langchain_community.vectorstores import FAISS
from rag.models import get_llm, get_embeddings
logger = logging.getLogger(__name__)
# Suprimir warnings de transformers
os.environ["TOKENIZERS_PARALLELISM"] = "false"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.environ.get("DB_DIR", BASE_DIR)

# Si DB_DIR no existe (cuando corre en Docker), crearlo.
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR, exist_ok=True)

VECTORSTORE_PATH = os.path.join(DB_DIR, "faiss_auracomm_index")

def get_s3_client():
    endpoint = os.getenv('MINIO_ENDPOINT')
    if endpoint and not endpoint.startswith('http'):
        endpoint = f"http://{endpoint}"
    return boto3.client(
        's3',
        endpoint_url=endpoint,
        aws_access_key_id=os.getenv('MINIO_ACCESS_KEY') or os.getenv('MINIO_ROOT_USER'),
        aws_secret_access_key=os.getenv('MINIO_SECRET_KEY') or os.getenv('MINIO_ROOT_PASSWORD')
    )

def fase1_cargar_pdfs_crudos():
    """Descarga los PDFs desde MinIO a la memoria RAM (Stateless) y extrae el texto."""
    bucket_name = os.getenv('MINIO_BUCKET_NAME')
    
    if not bucket_name:
        logger.warning("MINIO_BUCKET_NAME no configurado.")
        return []
        
    s3 = get_s3_client()
    documentos_crudos = []
    
    try:
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix='data/')
        objects = response.get('Contents', [])
        
        pdf_keys = [obj['Key'] for obj in objects if obj['Key'].lower().endswith('.pdf')]
        
        if not pdf_keys:
            logger.warning("No se encontraron PDFs en el bucket.")
            return []
            
        logger.info("Procesando %d PDFs en memoria RAM (Stateless) desde MinIO...", len(pdf_keys))
        for key in pdf_keys:
            # 1. Obtener el archivo directamente a la memoria RAM
            obj_response = s3.get_object(Bucket=bucket_name, Key=key)
            pdf_bytes = io.BytesIO(obj_response['Body'].read())
            
            # 2. Extraer texto al vuelo
            try:
                reader = pypdf.PdfReader(pdf_bytes)
                for i, page in enumerate(reader.pages):
                    texto = page.extract_text()
                    if texto:
                        # Limpieza y sanitización de texto para RAG
                        # 1. Unir palabras cortadas por guión y salto de línea (ej. infor- \n mación -> información)
                        texto = re.sub(r'-\s*\n\s*', '', texto)
                        # 2. Reemplazar los saltos de línea por un espacio
                        texto = texto.replace('\n', ' ')
                        # 3. Limpiar espacios múltiples o excesivos
                        texto = re.sub(r'\s+', ' ', texto).strip()
                        
                        # 3. Formatear como Documento de LangChain
                        doc = Document(
                            page_content=texto, 
                            metadata={"source": f"s3://{bucket_name}/{key}", "page": i}
                        )
                        documentos_crudos.append(doc)
            except Exception as e:
                logger.error("Error extrayendo texto de %s: %s", key, e)
            
    except ClientError as e:
        logger.error("Error accediendo a MinIO: %s", e)
        return []
        
    if not documentos_crudos:
        logger.warning("No se encontraron documentos válidos tras procesar los PDFs.")
    else:
        logger.info("Leídos %d documentos (páginas) en total directamente desde la memoria.", len(documentos_crudos))
        
    return documentos_crudos

def fase2_estructurar_documentos(documentos_crudos):
    """Fragmentación avanzada usando RecursiveCharacterTextSplitter."""
    if not documentos_crudos:
        return []
        
    # all-MiniLM-L6-v2 soporta hasta 256 tokens (~380 caracteres).
    # chunk_size=600 caracteres (~150 tokens) con overlap=100 garantiza
    # fragmentos precisos y semánticamente completos sin superar el límite de tokens de Groq (6000 TPM).
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=100,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    
    docs_procesados = text_splitter.split_documents(documentos_crudos)
    logger.info("Estructuración semántica completada: %d fragmentos generados.", len(docs_procesados))
    return docs_procesados

def get_pdfs_hash():
    """Calcula un hash MD5 combinando los ETags de MinIO para detectar modificaciones."""
    bucket_name = os.getenv('MINIO_BUCKET_NAME')
    if not bucket_name:
        return ""
        
    s3 = get_s3_client()
    hasher = hashlib.md5()
    
    try:
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix='data/')
        objects = response.get('Contents', [])
        pdf_objects = [obj for obj in objects if obj['Key'].lower().endswith('.pdf')]
        
        for obj in sorted(pdf_objects, key=lambda x: x['Key']):
            # Usar ETag directo de S3, es una forma rápida de verificar cambios
            hasher.update(obj['ETag'].encode('utf-8'))
            
        return hasher.hexdigest()
    except ClientError:
        return ""

def fase3_crear_base_vectorial(docs_procesados):
    """Convierte texto a vectores y guarda el índice FAISS."""
    current_hash = get_pdfs_hash()
    hash_file = f"{VECTORSTORE_PATH}_checksum.txt"
    
    if os.path.exists(VECTORSTORE_PATH) and os.path.exists(hash_file):
        with open(hash_file, "r") as f:
            saved_hash = f.read().strip()
            
        if saved_hash == current_hash:
            logger.info("VectorStore FAISS sincronizado. Omitiendo embeddings pesados.")
            return
        else:
            logger.info("Cambio detectado en los PDFs. Reconstruyendo la base de datos vectorial (FAISS)...")
            shutil.rmtree(VECTORSTORE_PATH)
            
    if docs_procesados:
        logger.info("Calculando Embeddings (HuggingFace locales)...")
        embeddings = get_embeddings()
        vectorstore = FAISS.from_documents(docs_procesados, embeddings)
        vectorstore.save_local(VECTORSTORE_PATH)
        
        # Guardar la nueva huella digital (checksum)
        with open(hash_file, "w") as f:
            f.write(current_hash)
            
        logger.info("FAISS Index creado en '%s'.", VECTORSTORE_PATH)

def obtener_retriever_avanzado():
    """Carga FAISS y devuelve el Retriever."""
    embeddings = get_embeddings()
    vectorstore = FAISS.load_local(VECTORSTORE_PATH, embeddings, allow_dangerous_deserialization=True)
    return vectorstore.as_retriever(
        search_type="mmr", 
        search_kwargs={"k": 6, "fetch_k": 25, "lambda_mult": 0.5}
    )
