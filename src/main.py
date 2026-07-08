# main.py
from core.app import AuraCommApp

def main():
    """Punto de entrada principal para ejecutar el agente AuraComm."""
    # La lógica de inicialización y el bucle CLI están encapsulados en AuraCommApp
    aplicacion = AuraCommApp(thread_id="sesion_produccion_005")
    aplicacion.run()

if __name__ == "__main__":
    main()
