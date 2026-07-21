import os
from langchain_huggingface import HuggingFaceEmbeddings

# ================================================================
# CONFIGURACIÓN DE IA HÍBRIDA (PROYECTO FINAL AURACOMM)
# ================================================================
# Arquitectura:
# 1. Embeddings: Local (HuggingFace all-MiniLM-L6-v2) - FAISS
# 2. Orquestador Principal (Cerebro B2B): Gemini API
# 3. Sub-Agente Lector (RAG): Groq API (Llama 3.1 8B)
# ================================================================

def get_llm(temperature=0):
    """
    Orquestador Principal: Gemini Flash
    Cerebro B2B: Maneja la lógica agentiva pesada, entiende instrucciones 
    complejas en español y razona la respuesta final.
    """
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    # Intentamos obtener la key, si no está lanzará un error claro
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Falta GEMINI_API_KEY en las variables de entorno.")
        
    return ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite", # Actualizado al modelo vigente en 2026
        google_api_key=api_key,
        temperature=temperature,
        max_retries=3
    )

def get_llm_rag(temperature=0):
    """
    Sub-Agente Lector (RAG): Llama 3.1 8B (Groq)
    Extracción ultrarrápida: Lee el texto que saca FAISS y devuelve JSON estructurado.
    """
    from langchain_groq import ChatGroq
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Falta GROQ_API_KEY en las variables de entorno.")
        
    return ChatGroq(
        model="llama-3.1-8b-instant",
        groq_api_key=api_key,
        temperature=temperature,
        max_retries=1
    )

def get_embeddings():
    """
    Embeddings y Base Vectorial: all-MiniLM-L6-v2
    Local / Offline: Pesa ~90MB y calcula vectores en CPU sin gastar API.
    """
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
