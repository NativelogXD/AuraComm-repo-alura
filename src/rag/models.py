import os
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
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
    """Devuelve la instancia configurada del modelo de Embeddings."""
    api_key = os.getenv('GEMINI_API_KEY')
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-2",
        google_api_key=api_key
    )
