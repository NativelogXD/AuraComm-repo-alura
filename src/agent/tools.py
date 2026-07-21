import json
import logging
from typing import Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from rag.models import get_llm, get_llm_rag
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough

logger = logging.getLogger(__name__)

from rag.rag import obtener_retriever_avanzado

# 1. Esquemas Centralizados (Pydantic)
from agent.schemas import ConsultaKPIInput, ConsultaPDFInput, ResultadoRAG
from data.semantic_layer import SemanticLayer

# 2. Clases de Herramientas (BaseTool)
class ConsultarKPITool(BaseTool):
    name: str = "consultar_kpi_empresarial"
    description: str = (
        "Úsala SOLO cuando el usuario pide un VALOR NUMÉRICO CALCULADO de la base de datos: "
        "conteos de clientes, promedios de ingresos, tasas de churn, máximos, o totales. "
        "EJEMPLOS de uso: '¿cuántos clientes activos hay?', '¿cuál es el promedio de ingresos?', '¿cuántos cancelaron?'. "
        "NO usar para: explicar qué significa una variable, responder preguntas técnicas o de troubleshooting, "
        "ni para preguntas sobre el nombre o definición de campos del CSV."
    )
    args_schema: Type[BaseModel] = ConsultaKPIInput
    
    _semantic_layer: object = None
    
    def inicializar(self, df_client, df_record):
        """Inicializa la Capa Semántica UNA SOLA VEZ (no en cada llamada)."""
        self._semantic_layer = SemanticLayer(df_client, df_record)
        logger.info("SemanticLayer inicializada con %d métricas del catálogo.", len(self._semantic_layer.catalogo))
    
    def _run(self, metric_name: str, filtro_dinamico: dict = None) -> str:
        if self._semantic_layer is None:
            return "Error: Capa Semántica no inicializada."
        return self._semantic_layer.ejecutar_kpi(metric_name, filtro_dinamico)

# ResultadoRAG es importado desde agent.schemas

def format_docs(docs):
    return "\n\n".join([doc.page_content for doc in docs])

class ConsultarPoliticasPDFTool(BaseTool):
    name: str = "consultar_politicas_pdf"
    description: str = (
        "Úsala para CUALQUIER pregunta conceptual, técnica o documental: "
        "(1) qué campo o variable del CSV representa un concepto (ej: '¿qué variable es la tarifa plana?'), "
        "(2) troubleshooting y diagnóstico (ej: '¿qué inspeccionar si drop_dat_Mean sube?'), "
        "(3) relación entre métricas o lógica de negocio, "
        "(4) políticas SLA, términos de facturación, privacidad y FAQ. "
        "Esta herramienta busca en los PDFs corporativos. Si la pregunta involucra un nombre de columna "
        "del CSV o un concepto técnico, SIEMPRE usar esta herramienta primero."
    )
    args_schema: Type[BaseModel] = ConsultaPDFInput
    
    # El retriever se inicializa una sola vez cuando la herramienta se instancia,
    # no en cada llamada _run. Esto evita abrir el índice FAISS repetidamente.
    _retriever: object = None
    
    def model_post_init(self, __context):
        """Inicializa el retriever FAISS una única vez al construir la herramienta."""
        try:
            self._retriever = obtener_retriever_avanzado()
        except Exception as e:
            logger.warning("FAISS no disponible al inicializar la herramienta: %s", e)
            self._retriever = None

    def _run(self, consulta: str) -> str:
        if self._retriever is None:
            return "Error: FAISS no inicializado."

        llm_rag = get_llm_rag()
        parser = JsonOutputParser(pydantic_object=ResultadoRAG)
        
        system_prompt = (
            "Eres un analista corporativo experto en extracción de información.\n"
            "REGLAS DE ORO (ANTI-ALUCINACIONES):\n"
            "1. Responde basándote ÚNICA y EXCLUSIVAMENTE en el texto proporcionado en 'Contexto'.\n"
            "2. Si la respuesta a la pregunta NO está en el contexto, DEBES establecer 'es_informacion_inventada' a True.\n"
            "3. NUNCA asumas, deduzcas ni inventes URLs, correos, nombres de documentos (como DOC-XXX) ni datos de contacto.\n"
            "4. Si el contexto está vacío o contiene información irrelevante, marca 'es_informacion_inventada' a True de inmediato.\n"
            "5. SI EL USUARIO PREGUNTA POR VARIABLES, PARÁMETROS O COLUMNAS, tu 'respuesta' DEBE INCLUIR el nombre literal exacto (ej. 'phones', 'models', 'actvsubs') extraído del contexto. NO des solo la definición, cita explícitamente las variables involucradas.\n"
            "6. PROHIBIDO ALUCINAR NÚMEROS: Si el usuario pregunta por un límite (ej. terabytes) o valor y NO aparece, marca 'es_informacion_inventada' a True.\n"
            "7. DETECCIÓN DE PREMISAS FALSAS: Si la pregunta asume algo (ej. 'cuántos días para borrar grabaciones') pero el contexto indica que esa característica NI SIQUIERA EXISTE o NUNCA se hace (ej. 'no grabamos audio'), DEBES responder explicando la política real en lugar de marcarlo como inventado.\n"
            "8. DEVUELVE ÚNICA Y EXCLUSIVAMENTE UN OBJETO JSON VÁLIDO. SIN TEXTO CONVERSACIONAL, SIN MARKDOWN (```json), SOLO EL RAW JSON.\n"
            "{format_instructions}\n\n"
            "Contexto:\n{context}"
        )
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ]).partial(format_instructions=parser.get_format_instructions())
        
        # LCEL Cadena RAG Avanzada Pura
        rag_chain = (
            {"context": self._retriever | format_docs, "input": RunnablePassthrough()}
            | prompt
            | llm_rag
            | parser
        )
        
        resultado = rag_chain.invoke(consulta)
        
        # Guardrail duro: Si el LLM interno admite que inventó (o no encontró) la info,
        # cortamos el paso del texto alucinado hacia el orquestador principal.
        if resultado.get("es_informacion_inventada") is True:
            return "ALERTA (Guardrail): No existe información en la base de datos documental sobre la consulta o documento solicitado. Responde al usuario que el documento no existe o no tienes información sobre ese tema."
            
        return json.dumps(resultado, ensure_ascii=False, indent=2)

class HerramientasFactory:
    def __init__(self, df_client, df_record):
        self.df_client = df_client
        self.df_record = df_record
        
    def obtener_tools(self):
        kpi_tool = ConsultarKPITool()
        kpi_tool.inicializar(self.df_client, self.df_record)
        
        pdf_tool = ConsultarPoliticasPDFTool()
        
        return [kpi_tool, pdf_tool]
