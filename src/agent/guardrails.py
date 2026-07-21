import json
from langchain_core.messages import AIMessage

def handle_llm_api_errors(error_str: str, valid_tool_names: list[str]) -> dict:
    """
    Parche de Emergencia: Atrapa y modulariza excepciones de LLMs (Gemini/Groq)
    para devolver mensajes de error amigables al usuario según el código de estado.
    """
    error_upper = error_str.upper()

    if "503" in error_upper or "UNAVAILABLE" in error_upper:
        fallback = AIMessage(content="[Aviso de Red] 🚦 Los servidores de Google Gemini están experimentando alta demanda en este momento. Por favor, espera unos segundos e intenta preguntar de nuevo.")
        return {"messages": [fallback]}
        
    if "400 INVALID_ARGUMENT" in error_upper or "FUNCTION CALL TURN" in error_upper:
        fallback = AIMessage(content="[Aviso de Historial] 🔄 Se detectó un error de sincronización en la conversación. Por favor, haz clic en el botón 'Limpiar Historial' e intenta de nuevo.")
        return {"messages": [fallback]}
        
    if "429" in error_upper or "TOO MANY REQUESTS" in error_upper:
        fallback = AIMessage(content="[Aviso de Límite] ⏳ Has excedido el límite de peticiones gratuitas. Por favor, espera un par de minutos antes de seguir preguntando.")
        return {"messages": [fallback]}
        
    if "413" in error_upper or "TOO LARGE" in error_upper or "RATE_LIMIT_EXCEEDED" in error_upper:
        fallback = AIMessage(content="[Aviso de Tokens] 📏 El contexto de la pregunta excedió el límite de la cuota del modelo. Por favor, simplifica tu pregunta.")
        return {"messages": [fallback]}
        
    if "404" in error_upper or "NOT FOUND" in error_upper:
        fallback = AIMessage(content="[Aviso de Modelo] ❌ El modelo de IA configurado no fue encontrado o tu API Key no tiene acceso a él. Revisa la variable GEMINI_API_KEY y el nombre del modelo en la configuración.")
        return {"messages": [fallback]}
    
    # Si todo falla, error genérico
    fallback = AIMessage(content="[Error de Red] 🛑 Ocurrió un error inesperado al conectar con el servidor de Inteligencia Artificial. Por favor, intenta más tarde.")
    return {"messages": [fallback]}

# (The function has been completely removed to clean up legacy XML parsing code)


