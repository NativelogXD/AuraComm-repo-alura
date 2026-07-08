import json
from typing import Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from rag.models import get_llm
from langchain_experimental.agents.agent_toolkits.pandas.base import create_pandas_dataframe_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough

from rag.rag import obtener_retriever_avanzado

# 1. Esquemas Centralizados (Pydantic)
from agent.schemas import ConsultaCSVInput, ConsultaPDFInput, CodigoPandas, ResultadoRAG

# 2. Clases de Herramientas (BaseTool)
class AnalizarDatosCSVTool(BaseTool):
    name: str = "analizar_datos_csv"
    description: str = "ÚTIL ÚNICAMENTE para analizar datos tabulares o matemáticos (MRR, Clientes, Latencia)."
    args_schema: Type[BaseModel] = ConsultaCSVInput
    
    df_client: object = None
    df_record: object = None
    
    def _run(self, consulta: str) -> str:
        if self.df_client is None and self.df_record is None:
            return "Error: CSVs no encontrados."
            
        from data.data_dictionary import PANDAS_INSTRUCTIONS
        
        llm_pandas = get_llm()
        
        # CodigoPandas es importado desde agent.schemas
            
        llm_with_schema = llm_pandas.with_structured_output(CodigoPandas)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", PANDAS_INSTRUCTIONS),
            ("human", "Consulta del usuario: {consulta}")
        ])
        
        cadena = prompt | llm_with_schema
        
        try:
            resultado_llm = cadena.invoke({"consulta": consulta})
            codigo = resultado_llm.codigo.replace("```python", "").replace("```", "").strip()
            
            locals_dict = {'df_client': self.df_client, 'df_record': self.df_record}
            exec(codigo, {}, locals_dict)
            
            if 'final_result' in locals_dict:
                # Retornar el resultado directamente como cadena determinista
                return f"EJECUCIÓN DETERMINISTA EXITOSA.\nCÓDIGO EJECUTADO:\n{codigo}\n\nRESULTADO CRUDO:\n{str(locals_dict['final_result'])}"
            else:
                return "Error: La IA no guardó el resultado en la variable 'final_result'."
        except Exception as e:
            return f"Error ejecutando código determinista: {str(e)}"

# ResultadoRAG es importado desde agent.schemas

def format_docs(docs):
    return "\n\n".join([doc.page_content for doc in docs])

class ConsultarPoliticasPDFTool(BaseTool):
    name: str = "consultar_politicas_pdf"
    description: str = "ÚTIL ÚNICAMENTE para buscar políticas corporativas, documentación técnica o arquitectura en los PDFs (SLA, Privacidad, FAQ)."
    args_schema: Type[BaseModel] = ConsultaPDFInput
    
    def _run(self, consulta: str) -> str:
        try:
            retriever = obtener_retriever_avanzado()
        except Exception:
            return "Error: FAISS no inicializado."

        llm_rag = get_llm()
        parser = JsonOutputParser(pydantic_object=ResultadoRAG)
        
        system_prompt = (
            "Eres un analista corporativo. Responde basándote SOLO en el contexto proporcionado.\n"
            "REGLA CRÍTICA: NUNCA inventes URLs, enlaces, correos ni datos de contacto que no estén EXPLÍCITAMENTE escritos en el contexto.\n"
            "{format_instructions}\n\n"
            "Contexto:\n{context}"
        )
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ]).partial(format_instructions=parser.get_format_instructions())
        
        # LCEL Cadena RAG Avanzada Pura
        rag_chain = (
            {"context": retriever | format_docs, "input": RunnablePassthrough()}
            | prompt
            | llm_rag
            | parser
        )
        
        resultado = rag_chain.invoke(consulta)
        return json.dumps(resultado, ensure_ascii=False, indent=2)

class HerramientasFactory:
    def __init__(self, df_client, df_record):
        self.df_client = df_client
        self.df_record = df_record
        
    def obtener_tools(self):
        csv_tool = AnalizarDatosCSVTool()
        csv_tool.df_client = self.df_client
        csv_tool.df_record = self.df_record
        
        pdf_tool = ConsultarPoliticasPDFTool()
        
        return [csv_tool, pdf_tool]
