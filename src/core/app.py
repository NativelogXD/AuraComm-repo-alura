from core.setup_env import SetupEnvironment
from ui.cli_interface import CLIHandler
from agent.tools import HerramientasFactory
from agent.orcuestrator import crear_orquestador

class AuraCommApp:
    def __init__(self, thread_id="sesion_produccion_005"):
        # 1. Configurar Entorno (Carga de variables, FAISS y CSVs)
        df_client, df_record = SetupEnvironment.inicializar()
        
        # 2. Construir Orquestador (LangGraph y Herramientas)
        factory = HerramientasFactory(df_client, df_record)
        app_graph = crear_orquestador(factory.obtener_tools())
        
        # 3. Inicializar Interfaz (Lógica de presentación y CLI)
        self.cli = CLIHandler(app_graph, thread_id)

    def run(self):
        """Inicia la aplicación delegando el bucle a la interfaz CLI."""
        self.cli.iniciar_chat()
