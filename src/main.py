import os
from dotenv import load_dotenv

# 1. Cargamos el entorno para las keys
load_dotenv()

# 2. Importamos nuestros módulos locales
from rag.rag import (
    fase1_cargar_pdfs_crudos,
    fase2_estructurar_documentos,
    fase3_crear_base_vectorial
)
from data_cleaning import fase4_limpiar_csvs
from tools import HerramientasFactory
from orcuestrator import crear_orquestador

from langchain_core.messages import HumanMessage

def inicializar_entorno():
    """Configura los índices de FAISS y carga los CSVs limpios."""
    print("\n--- INICIALIZANDO SISTEMA AURACOMM ---")
    
    docs_crudos = fase1_cargar_pdfs_crudos()
    if docs_crudos:
        docs_procesados = fase2_estructurar_documentos(docs_crudos)
        fase3_crear_base_vectorial(docs_procesados)
        
    df_client, df_record = fase4_limpiar_csvs()
    return df_client, df_record

def main():
    df_client, df_record = inicializar_entorno()
    factory = HerramientasFactory(df_client, df_record)
    herramientas = factory.obtener_tools()
    
    app_graph = crear_orquestador(herramientas)
    config = {"configurable": {"thread_id": "sesion_produccion_001"}}

    print("\n" + "="*60)
    print("[AuraComm] Digital - Agente B2B (Versión Gemini)")
    print("Escribe 'salir' para terminar la conversación.")
    print("Las operaciones sensibles pedirán aprobación (HITL).")
    print("="*60 + "\n")
    
    while True:
        estado_actual = app_graph.get_state(config)
        if estado_actual.next == ('action',):
            print("\n[⚠️ ALERTA HITL]: El agente solicita ejecutar una herramienta interna (CSVs o PDFs).")
            decision = input("¿Aprobar ejecución? (s/n): ").strip().lower()
            
            if decision == 's':
                print("[✔️ Aprobado. Procesando...]")
                eventos = app_graph.stream(None, config, stream_mode="values")
                for event in eventos:
                    msg = event["messages"][-1]
                    if not getattr(msg, 'tool_calls', None) and msg.content and getattr(msg, 'type', None) == 'ai':
                        print(f"\n[🤖 AuraComm]: {msg.content}\n")
                continue
            else:
                print("[❌ Rechazado.]")
                break
        
        pregunta = input("Usuario: ")
        if pregunta.lower() in ['salir', 'exit', 'quit']:
            print("¡Hasta luego! Memoria guardada.")
            break
            
        print("-" * 40)
        eventos = app_graph.stream(
            {"messages": [HumanMessage(content=pregunta)]},
            config,
            stream_mode="values"
        )
        
        for event in eventos:
            msg = event["messages"][-1]
            if getattr(msg, 'tool_calls', None):
                pass
            elif getattr(msg, 'type', None) == 'ai' and msg.content:
                print(f"\n[🤖 AuraComm]: {msg.content}\n")

if __name__ == "__main__":
    main()
