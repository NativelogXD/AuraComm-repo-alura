class GestorExcepcionesAuraComm:
    """
    Clase orientada a objetos para encapsular y manejar las excepciones del orquestador AuraComm.
    Permite modularizar las plantillas de error visuales.
    """
    
    @staticmethod
    def manejar_error(excepcion: Exception) -> bool:
        """
        Evalúa el error y despliega su plantilla correspondiente en la consola.
        Retorna True si el error es transitorio/recuperable (ej: Rate Limit de API),
        o False si es un error crítico que requiere detener la ejecución.
        """
        error_str = str(excepcion)
        
        if "RESOURCE_EXHAUSTED" in error_str or "429" in error_str:
            print("\n" + "="*60)
            print("[AVISO DE SISTEMA]: Tokens gratuitos agotados.")
            print("Has alcanzado el límite de peticiones de la capa gratuita de Gemini.")
            print("> Por favor, espera entre 1 y 2 minutos e intentalo nuevamente.")
            print("="*60 + "\n")
            return True
            
        else:
            print(f"\n[ERROR CRITICO]: {error_str}\n")
            return False
