from langchain_core.messages import HumanMessage
from excepciones.manejador_errores import GestorExcepcionesAuraComm

class CLIHandler:
    def __init__(self, app_graph, thread_id="sesion_produccion_005"):
        self.app_graph = app_graph
        self.config = {"configurable": {"thread_id": thread_id}}

    def procesar_hitl(self, estado_actual):
        """Maneja la aprobación humana (Human-In-The-Loop) antes de ejecutar herramientas."""
        print("\n[⚠️ ALERTA HITL]: El agente solicita ejecutar una herramienta interna.")
        
        # Extraer y mostrar exactamente qué va a ejecutar (Transparencia HITL)
        ultimo_mensaje = estado_actual.values["messages"][-1]
        if getattr(ultimo_mensaje, 'tool_calls', None):
            for tc in ultimo_mensaje.tool_calls:
                print(f" -> Herramienta: {tc['name']}")
                print(f" -> Argumentos: {tc['args']}")
                
        decision = input("\n¿Aprobar ejecución? (s = sí / n = no): ").strip().lower()
        
        if decision == 's':
            print("[✔️ Aprobado. Procesando...]")
            try:
                eventos = self.app_graph.stream(None, self.config, stream_mode="values")
                self._imprimir_eventos(eventos)
            except Exception as e:
                GestorExcepcionesAuraComm.manejar_error(e)
            return True
        else:
            print("[❌ Rechazado.]")
            return False

    def _imprimir_eventos(self, eventos):
        """Imprime las respuestas de la IA ignorando mensajes intermedios de herramientas."""
        for event in eventos:
            msg = event["messages"][-1]
            if not getattr(msg, 'tool_calls', None) and msg.content and getattr(msg, 'type', None) == 'ai':
                print(f"\n[🤖 AuraComm]: {msg.content}\n")

    def iniciar_chat(self):
        """Bucle principal de la interfaz de línea de comandos (CLI)."""
        print("\n" + "="*60)
        print("[AuraComm] Digital - Agente B2B (Arquitectura Determinista)")
        print("Escribe 'salir' para terminar la conversación.")
        print("Las operaciones sensibles pedirán aprobación (HITL).")
        print("="*60 + "\n")
        
        while True:
            # 1. Comprobar si hay una herramienta pausada esperando HITL
            estado_actual = self.app_graph.get_state(self.config)
            if estado_actual.next == ('action',):
                if not self.procesar_hitl(estado_actual):
                    break
                continue
            
            # 2. Flujo normal del usuario
            pregunta = input("Usuario: ")
            if pregunta.lower() in ['salir', 'exit', 'quit']:
                print("¡Hasta luego! Memoria guardada.")
                break
                
            print("-" * 40)
            try:
                eventos = self.app_graph.stream(
                    {"messages": [HumanMessage(content=pregunta)]},
                    self.config,
                    stream_mode="values"
                )
                self._imprimir_eventos(eventos)
            except Exception as e:
                recuperable = GestorExcepcionesAuraComm.manejar_error(e)
                if not recuperable:
                    break
