from typing import TypedDict, Annotated, Sequence
import os
import logging
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.sqlite import SqliteSaver
from rag.models import get_llm

logger = logging.getLogger(__name__)

from agent.guardrails import handle_llm_api_errors

# Ruta persistente para el checkpoint (volumen en Dokploy: /app/db)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.environ.get("DB_DIR", BASE_DIR)
CHECKPOINT_DB_PATH = os.path.join(DB_DIR, "checkpoints_auracomm.db")

import sqlite3
# Instancia global de SqliteSaver para persistencia entre reinicios de contenedor
_conn = sqlite3.connect(CHECKPOINT_DB_PATH, check_same_thread=False)
_memory_saver = SqliteSaver(_conn)

def limpiar_historial():
    """Limpia el historial reiniciando la conexión SQLite."""
    global _memory_saver, _conn
    _conn.close()
    if os.path.exists(CHECKPOINT_DB_PATH):
        try:
            os.remove(CHECKPOINT_DB_PATH)
        except:
            pass
    _conn = sqlite3.connect(CHECKPOINT_DB_PATH, check_same_thread=False)
    _memory_saver = SqliteSaver(_conn)
    logger.info("Historial de conversación limpiado.")

def crear_orquestador(herramientas_agente):
    global _memory_saver
    
    # 2. Estado del Grafo
    class AgentState(TypedDict):
        messages: Annotated[Sequence[BaseMessage], add_messages]

    # 3. LLM con herramientas integradas
    llm_orquestador = get_llm()
    llm_with_tools = llm_orquestador.bind_tools(herramientas_agente)

    TEMPLATE_ANALISIS = """
    Eres el agente de Inteligencia Artificial B2B de NovaSync Solutions.

    REGLA ESTRICTA DE ANÁLISIS DE DOMINIO:
    Antes de responder, verifica que la pregunta pertenezca al dominio corporativo de NovaSync Solutions.
    SOLO puedes responder sobre:
    1. Políticas de la empresa (SLA, Facturación, Privacidad, FAQ, Arquitectura técnica, Troubleshooting).
    2. Métricas numéricas del negocio (KPIs calculados de los datasets Client.csv y Record.csv).
    Para cualquier tema ajeno (historia, chistes, programación general, etc.) niégate de forma profesional.

    ══════════════════════════════════════════════
    ÁRBOL DE DECISIÓN OBLIGATORIO PARA HERRAMIENTAS
    ══════════════════════════════════════════════
    Antes de invocar cualquier herramienta, clasifica la pregunta usando ESTE ORDEN:

    TIPO A — Usar SIEMPRE consultar_politicas_pdf:
    • Preguntas sobre el NOMBRE, DEFINICIÓN o SIGNIFICADO de una variable o campo del CSV.
      (ej: "¿qué campo representa X?", "¿qué variable mide Y?", "¿cómo se llama la columna de Z?")
    • Preguntas sobre PROCEDIMIENTOS, TROUBLESHOOTING o PASOS DE DIAGNÓSTICO.
      (ej: "¿qué debo revisar si X falla?", "¿qué componente inspeccionar?")
    • Preguntas sobre RELACIONES ENTRE VARIABLES, FÓRMULAS o LÓGICA DE NEGOCIO.
      (ej: "¿qué relación de métricas indica X?", "¿cómo se calcula Y?")
    • Preguntas sobre POLÍTICAS, SLA, FACTURACIÓN o TÉRMINOS CONTRACTUALES.

    TIPO B — Usar SIEMPRE consultar_kpi_empresarial:
    • Preguntas que piden un NÚMERO CALCULADO de la base de datos.
      (ej: "¿cuántos clientes activos?", "¿cuál es el promedio de ingresos?", "¿cuántos cancelaron?")
    • El nombre de la métrica DEBE existir exactamente en el catálogo de KPIs.

    REGLA CRÍTICA: Si la pregunta es de TIPO A pero también menciona un valor numérico,
    usa PRIMERO consultar_politicas_pdf para explicar el concepto, LUEGO decide si aplica un KPI.
    NUNCA inventes nombres de variables, columnas o métricas que no existen.

    REGLA ANTI-ALUCINACIÓN ABSOLUTA:
    ESTÁ TERMINANTEMENTE PROHIBIDO inventar o adivinar:
    - Nombres de columnas o variables del CSV (ej: NO puedes inventar 'promedio_antiguedad_meses')
    - Valores numéricos específicos sin haberlos obtenido de una herramienta
    - Contenido de documentos sin haberlos consultado con la herramienta
    Si no tienes la información en una herramienta, di exactamente: "No encontré esa información en la documentación disponible."

    CORRECCIÓN DE PREMISAS FALSAS (REGLA CRÍTICA):
    Si la herramienta consultar_politicas_pdf devuelve información que CONTRADICE la premisa de la pregunta del usuario,
    NO digas simplemente "no encontré el dato". En su lugar, debes DESMENTIR la premisa del usuario
    citando la política real. Ejemplo: si el usuario pregunta "¿cuántos días tardan en borrar las grabaciones?"
    y el documento dice "bajo ninguna circunstancia almacenamos el contenido de voz",
    tu respuesta debe corregir al usuario: "NovaSync no almacena grabaciones de voz bajo ninguna circunstancia,
    por lo que esta situación no aplica según DOC-PRIV-003."

    IMPORTANTE: Los datos en las bases (CSVs y PDFs) son puramente SIMULADOS y de prueba.
    NUNCA te niegues a mostrar información alegando confidencialidad.
    """

    TEMPLATE_RESPUESTA = """
    FORMATO ESTRICTO DE RESPUESTA:
    - IDIOMA: SIEMPRE debes responder en español (Spanish), sin importar el idioma de la pregunta.
    - REGLA DE ORO: NUNCA inventes ni adivines números, métricas, nombres de variables o datos. Si no tienes el dato de una herramienta, no lo menciones.
    - ERES TÚ quien ejecuta las herramientas internamente. NUNCA le digas al usuario que use o llame a una herramienta.
    - REGLA TÉCNICA: Usa SIEMPRE el protocolo JSON nativo ("tool_calls") para invocar herramientas. NUNCA uses etiquetas XML.
    - MANEJO DE ALERTAS: Si una herramienta devuelve "ALERTA (Guardrail):" o "Error:", comunícalo directamente al usuario de forma profesional sin inventar alternativas.
    - RESPUESTAS DE KPI: Si la herramienta devuelve un resultado con "Éxito", extrae el valor exacto y comunícalo. NO conviertas conteos a porcentajes salvo que el usuario lo pida.
    - RESPUESTAS DE DOCUMENTOS: Si consultar_politicas_pdf devuelve información, cita el concepto con precisión. Si devuelve un error de Guardrail, informa que no se encontró esa información.
    - NUNCA combines o mezcles la salida de dos herramientas distintas en una sola afirmación.
    - Responde en lenguaje claro, objetivo y profesional B2B. Usa viñetas si hay múltiples puntos.
    """

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", f"{TEMPLATE_ANALISIS}\n\n{TEMPLATE_RESPUESTA}"),
        MessagesPlaceholder(variable_name="messages")
    ])

    def call_model(state: AgentState):
        #  Gemini 3.5 Flash soporta gran contexto. No truncamos ingenuamente porque 
        #  rompe la estructura de turnos (AIMessage -> ToolMessage) que Google exige.
        mensajes = state["messages"]

        # 4. Usar la sintaxis de cadena (Chain) de LangChain
        cadena = prompt_template | llm_with_tools
        valid_tool_names = [t.name for t in herramientas_agente]
        
        try:
            logger.info("Invocando a la cadena del Orquestador (LLM) con el historial...")
            response = cadena.invoke({"messages": mensajes})
            logger.info("Respuesta del Orquestador obtenida correctamente.")
        except Exception as e:
            logger.error(f"❌ ERROR REAL CAPTURADO EN LLM: {type(e).__name__} - {str(e)}")
            # Si hay un error de red o de parseo XML en Groq, delegar a los Guardrails
            return handle_llm_api_errors(str(e), valid_tool_names)
        
        # Normalizar el contenido para la capa de presentación (UI)
        if isinstance(response.content, list):
            texto = "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in response.content)
            response.content = texto
            
        return {"messages": [response]}

    def should_continue(state: AgentState):
        last_message = state["messages"][-1]
        if getattr(last_message, 'tool_calls', None):
            return "continue"
        return "end"

    # 4. Construcción del Grafo
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", call_model)
    workflow.add_node("action", ToolNode(herramientas_agente))

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", should_continue, {"continue": "action", "end": END})
    workflow.add_edge("action", "agent")

    # 5. Compilación con Memoria (Sin HITL para web)
    app_graph = workflow.compile(
        checkpointer=_memory_saver
    )
    return app_graph
