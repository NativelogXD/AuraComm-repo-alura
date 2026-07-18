import re
import json
from langchain_core.messages import AIMessage

def handle_groq_400_error(error_str: str, valid_tool_names: list[str]) -> dict:
    """
    Parche de Emergencia: Atrapa el Error 400 (BadRequest) de Groq.
    Si el LLM (Llama 3) no cierra correctamente la etiqueta </function>,
    extrae la intención cortada y reconstruye el AIMessage para evitar 
    que el servidor colapse.
    """
    if "failed_generation" in error_str:
        match = re.search(r"<function=([^>]+)>(\{.*?\})", error_str)
        if match:
            tool_name = match.group(1).strip()
            
            if tool_name in valid_tool_names:
                try:
                    # Limpiar strings escapados en el volcado de error de Groq
                    args_str = match.group(2).replace("\\'", "'").replace('\\"', '"')
                    
                    # Asegurar que el JSON cierra correctamente
                    last_brace = args_str.rfind('}')
                    if last_brace != -1:
                        args_str = args_str[:last_brace+1]
                        
                    tool_args = json.loads(args_str)
                    
                    # Crear un mensaje artificial para salvar la ejecución
                    response = AIMessage(
                        content="",
                        tool_calls=[{
                            "name": tool_name,
                            "args": tool_args,
                            "id": f"call_manual_{tool_name}"
                        }]
                    )
                    return {"messages": [response]}
                except Exception:
                    pass
    
    # Si la recuperación falla, evitar que Streamlit explote
    fallback = AIMessage(content="[Error de Red] El servidor de IA generó una sintaxis incompleta y abortó la petición. Por favor, intenta hacer la pregunta con otras palabras.")
    return {"messages": [fallback]}

def clean_llm_hallucinations(response: AIMessage, valid_tool_names: list[str]) -> AIMessage:
    """
    Parche de Ingeniería Avanzada: Interceptar Tool Calling XML de Groq/Llama.
    Previene que el LLM inyecte herramientas inexistentes (alucinaciones)
    en la base de datos local SQLite, lo cual provocaría errores 400 subsecuentes.
    """
    if not getattr(response, "tool_calls", None) and "</function>" in response.content:
        match = re.search(r'<([^>]+)>(\{.*?\})</function>', response.content, re.DOTALL)
        if match:
            tool_name = match.group(1).strip()
            
            # Solo interceptar si la herramienta es válida para este orquestador
            if tool_name in valid_tool_names:
                try:
                    tool_args = json.loads(match.group(2))
                    response.tool_calls = [{
                        "name": tool_name,
                        "args": tool_args,
                        "id": f"call_manual_{tool_name}"
                    }]
                    response.content = "" # Ocultar la etiqueta XML al usuario
                except Exception:
                    pass
            else:
                # Si alucina una herramienta que no existe, limpiar el texto malicioso
                response.content = response.content.replace(match.group(0), "")
                
    return response
