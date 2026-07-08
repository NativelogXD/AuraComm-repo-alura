import os
import logging
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

def fase3_crear_base_vectorial(docs_procesados):
    """Convierte texto a vectores y guarda el índice FAISS."""
    if os.path.exists(VECTORSTORE_PATH):
        print("VectorStore FAISS ya existe. Omitiendo embeddings pesados.")
        return
        
    if docs_procesados:
        print("Calculando Embeddings (Gemini)...")
        embeddings = get_embeddings()
        vectorstore = FAISS.from_documents(docs_procesados, embeddings)
        vectorstore.save_local(VECTORSTORE_PATH)
        print(f" FAISS Index creado en '{VECTORSTORE_PATH}'.")

def obtener_retriever_avanzado():
    """Carga FAISS y devuelve el MultiQueryRetriever."""
    embeddings = get_embeddings()
    vectorstore = FAISS.load_local(VECTORSTORE_PATH, embeddings, allow_dangerous_deserialization=True)
    
    llm = get_llm()
    return MultiQueryRetriever.from_llm(
        retriever=vectorstore.as_retriever(search_kwargs={"k": 4}),
        llm=llm
    )
