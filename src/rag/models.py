import os
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

def get_llm(temperature=0):
    """Devuelve la instancia configurada del LLM (Gemini)."""
    api_key = os.getenv('GEMINI_API_KEY')
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=api_key,
        temperature=temperature
    )

def get_embeddings():
    """Devuelve la instancia configurada del modelo de Embeddings."""
    api_key = os.getenv('GEMINI_API_KEY')
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-2",
        google_api_key=api_key
    )
