import os
from dotenv import load_dotenv

from rag.rag import (
    fase1_cargar_pdfs_crudos,
    fase2_estructurar_documentos,
    fase3_crear_base_vectorial
)
from data.data_cleaning import fase4_limpiar_csvs

class SetupEnvironment:
    @staticmethod
    def inicializar():
        """Configura variables de entorno, índices de FAISS y carga los CSVs."""
        load_dotenv()
        
        print("\n--- INICIALIZANDO SISTEMA AURACOMM ---")
        
        # 1. RAG y Base Vectorial
        docs_crudos = fase1_cargar_pdfs_crudos()
        if docs_crudos:
            docs_procesados = fase2_estructurar_documentos(docs_crudos)
            fase3_crear_base_vectorial(docs_procesados)
            
        # 2. Datos tabulares limpios
        df_client, df_record = fase4_limpiar_csvs()
        return df_client, df_record
