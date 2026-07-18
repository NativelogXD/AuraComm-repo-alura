import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq

def get_llm(temperature=0):
    """Devuelve la instancia configurada del LLM (Llama 3.1 8B Instant).
    Elegido por su límite altísimo de peticiones (ideal para evaluación continua)."""
    api_key = os.getenv('GROQ_API_KEY')
    return ChatGroq(
        model="llama-3.1-8b-instant",
        groq_api_key=api_key,
        temperature=temperature
    )

def get_embeddings():
    """Devuelve la instancia configurada del modelo local de Embeddings Open Source."""
    return HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )
