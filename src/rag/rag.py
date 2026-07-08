import os
import logging
import hashlib
import shutil
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_text_splitters import CharacterTextSplitter
from transformers import AutoTokenizer
from langchain_community.vectorstores import FAISS
from langchain_classic.retrievers.multi_query import MultiQueryRetriever
from rag.models import get_llm, get_embeddings

logging.getLogger("langchain_classic.retrievers.multi_query").setLevel(logging.WARNING)
# Suprimir warnings de transformers
os.environ["TOKENIZERS_PARALLELISM"] = "false"

VECTORSTORE_PATH = "faiss_auracomm_index"

def fase1_cargar_pdfs_crudos():
    """Lee todos los PDFs usando DirectoryLoader (Carga Avanzada)."""
    if not os.path.exists("data"):
        print(" Directorio data/ no encontrado.")
        return []
        
    # Carga avanzada por lotes usando glob patterns
    loader = DirectoryLoader("data", glob="**/*.pdf", loader_cls=PyPDFLoader)
    documentos_crudos = loader.load()
    
    if not documentos_crudos:
        print(" No se encontraron PDFs en el directorio data/.")
    else:
        print(f" Leídos {len(documentos_crudos)} documentos (páginas) en total mediante DirectoryLoader.")
        
    return documentos_crudos

def fase2_estructurar_documentos(documentos_crudos):
    """Fragmentación avanzada usando tokenizador local de Hugging Face."""
    if not documentos_crudos:
        return []
        
    print("Descargando/Cargando Tokenizador de HuggingFace...")
    # Tokenizador multilingüe robusto para fragmentación por tokens reales
    tokenizer = AutoTokenizer.from_pretrained("intfloat/multilingual-e5-small")
    
    text_splitter = CharacterTextSplitter.from_huggingface_tokenizer(
        tokenizer,
        chunk_size=300,  # Límite por Tokens (no por caracteres)
        chunk_overlap=50
    )
    
    docs_procesados = text_splitter.split_documents(documentos_crudos)
    print(f"Estructuración semántica completada: {len(docs_procesados)} fragmentos generados respetando tokens.")
    return docs_procesados

def get_pdfs_hash():
    """Calcula un hash MD5 de todos los PDFs para detectar modificaciones."""
    if not os.path.exists("data"):
        return ""
    hasher = hashlib.md5()
    for filename in sorted(os.listdir("data")):
        if filename.endswith(".pdf"):
            filepath = os.path.join("data", filename)
            with open(filepath, "rb") as f:
                hasher.update(f.read())
    return hasher.hexdigest()

def fase3_crear_base_vectorial(docs_procesados):
    """Convierte texto a vectores y guarda el índice FAISS."""
    current_hash = get_pdfs_hash()
    hash_file = f"{VECTORSTORE_PATH}_checksum.txt"
    
    if os.path.exists(VECTORSTORE_PATH) and os.path.exists(hash_file):
        with open(hash_file, "r") as f:
            saved_hash = f.read().strip()
            
        if saved_hash == current_hash:
            print("VectorStore FAISS sincronizado. Omitiendo embeddings pesados.")
            return
        else:
            print("⚠️ Cambio detectado en los PDFs. Reconstruyendo la base de datos vectorial (FAISS)...")
            shutil.rmtree(VECTORSTORE_PATH)
            
    if docs_procesados:
        print("Calculando Embeddings (Gemini)...")
        embeddings = get_embeddings()
        vectorstore = FAISS.from_documents(docs_procesados, embeddings)
        vectorstore.save_local(VECTORSTORE_PATH)
        
        # Guardar la nueva huella digital (checksum)
        with open(hash_file, "w") as f:
            f.write(current_hash)
            
        print(f" FAISS Index creado en '{VECTORSTORE_PATH}'.")

def obtener_retriever_avanzado():
    """Carga FAISS y devuelve el MultiQueryRetriever."""
    embeddings = get_embeddings()
    vectorstore = FAISS.load_local(VECTORSTORE_PATH, embeddings, allow_dangerous_deserialization=True)
    
    llm = get_llm()
    return MultiQueryRetriever.from_llm(
        retriever=vectorstore.as_retriever(search_kwargs={"k": 2}), # Reducido a 2 para ahorrar tokens
        llm=llm
    )
