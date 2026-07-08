import sqlite3
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.sqlite import SqliteSaver
from rag.models import get_llm

def crear_orquestador(herramientas_agente):
    # 1. Memoria persistente SQLite
    conn = sqlite3.connect("checkpoints_auracomm.db", check_same_thread=False)
    memory = SqliteSaver(conn)

    # 2. Estado del Grafo
    class AgentState(TypedDict):
        messages: Annotated[Sequence[BaseMessage], add_messages]

    # 3. LLM con herramientas integradas
    llm_orquestador = get_llm()
    llm_with_tools = llm_orquestador.bind_tools(herramientas_agente)

    TEMPLATE_ANALISIS = """
    Eres AuraComm Digital, el agente de Inteligencia Artificial B2B de NovaSync Solutions.
    
    REGLA ESTRICTA DE ANÁLISIS DE DOMINIO:
    Antes de responder o usar cualquier herramienta, analiza si la pregunta del usuario pertenece al dominio corporativo.
    SOLO tienes permitido responder sobre:
    1. Políticas de la empresa (Acuerdos SLA, Facturación, Privacidad, FAQ, Arquitectura técnica).
    2. Datos internos de clientes (Client.csv) y métricas de rendimiento (Record.csv, MRR, Latencia).
    
    Si el usuario pregunta sobre CUALQUIER otro tema ajeno a la corporación (ej: historia, programación general, chistes, cultura popular, etc.):
    DEBES NEGARTE INMEDIATAMENTE de forma cortés, explicando que eres un agente corporativo exclusivo de AuraComm y no estás autorizado para otros temas. No uses ninguna herramienta para temas fuera de dominio.
    """

    TEMPLATE_RESPUESTA = """
    FORMATO ESTRICTO DE RESPUESTA:
    Cuando la consulta sea válida y corporativa:
    - Genera un resumen utilizando un lenguaje claro, objetivo y altamente profesional.
    - La comunicación del resultado debe ser lo más sencilla posible para un gerente o cliente B2B.
    - Si usaste herramientas (CSVs o PDFs), ve directo al grano con los datos o políticas encontradas.
    - Usa viñetas si hay múltiples puntos importantes.
    """

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", f"{TEMPLATE_ANALISIS}\n\n{TEMPLATE_RESPUESTA}"),
        MessagesPlaceholder(variable_name="messages")
    ])

    def call_model(state: AgentState):
        # 4. Usar la sintaxis de cadena (Chain) de LangChain
        cadena = prompt_template | llm_with_tools
        response = cadena.invoke({"messages": state["messages"]})
        
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

    # 5. Compilación con HITL y Memoria
    app_graph = workflow.compile(
        checkpointer=memory,
        interrupt_before=["action"]  # Pausa antes de ejecutar herramienta (HITL)
    )
    return app_graph
