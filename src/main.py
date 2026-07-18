import streamlit as st
import sys

# Forzar codificación UTF-8 para evitar errores de consola en Windows (charmap)
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from langchain_core.messages import HumanMessage
from core.setup_env import SetupEnvironment
from agent.tools import HerramientasFactory
from agent.orcuestrator import crear_orquestador

# 1. Configuración básica de la página
st.set_page_config(page_title="Terminal NovaSync", layout="wide")

# Inicialización Singleton con Caché para evitar recargar RAG y FAISS
@st.cache_resource(show_spinner=False)
def inicializar_agente():
    df_client, df_record = SetupEnvironment.inicializar()
    factory = HerramientasFactory(df_client, df_record)
    return crear_orquestador(factory.obtener_tools())

app_graph = inicializar_agente()
config = {"configurable": {"thread_id": "sesion_web_001"}}

# 2. LA MAGIA: Inyección de CSS para simular la consola pura
estilo_consola = """
<style>
    /* Fondo negro profundo para toda la app */
    .stApp {
        background-color: #050505;
    }
    
    /* Forzar color verde neón y fuente monoespaciada para todo el texto */
    html, body, [class*="css"], p, div, span, h1, h2, h3 {
        color: #00FF41 !important;
        font-family: 'Courier New', Courier, monospace !important;
    }

    /* Ocultar el menú superior y el pie de página de Streamlit para que no parezca una web */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Estilo para la barra de chat donde el usuario escribe */
    .stChatInputContainer {
        background-color: #000000 !important;
        border: 1px solid #00FF41 !important;
    }
    .stChatInputContainer textarea {
        color: #00FF41 !important;
    }
</style>
"""
st.markdown(estilo_consola, unsafe_allow_html=True)

# 3. Encabezado con tu Arte ASCII
st.markdown("""
```text
███╗   ██╗ ██████╗ ██╗   ██╗ █████╗ ███████╗██╗   ██╗███╗   ██╗ ██████╗
████╗  ██║██╔═══██╗██║   ██║██╔══██╗██╔════╝╚██╗ ██╔╝████╗  ██║██╔════╝
██╔██╗ ██║██║   ██║██║   ██║███████║███████╗ ╚████╔╝ ██╔██╗ ██║██║     
██║╚██╗██║██║   ██║╚██╗ ██╔╝██╔══██║╚════██║  ╚██╔╝  ██║╚██╗██║██║     
██║ ╚████║╚██████╔╝ ╚████╔╝ ██║  ██║███████║   ██║   ██║ ╚████║╚██████╗
╚═╝  ╚═══╝ ╚═════╝   ╚═══╝  ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═══╝ ╚═════╝
v1.0.0 Enterprise - Boot Sequence Initiated...
```
""")
st.markdown("---")

# 4. Memoria del chat para simular el desplazamiento de la terminal
if "historial" not in st.session_state:
    st.session_state.historial = [
        {"role": "sys", "content": "Conexión a MinIO [OK]"},
        {"role": "sys", "content": "Base de datos FAISS cargada en memoria [OK]"},
        {"role": "sys", "content": "Esperando input del usuario..."}
    ]

# Dibujar todos los mensajes anteriores
for msg in st.session_state.historial:
    if msg["role"] == "sys":
        st.markdown(f"[{msg['role'].upper()}] {msg['content']}")
    elif msg["role"] == "user":
        st.markdown(f"[{msg['role'].upper()}] > {msg['content']}")
    else:
        st.markdown(f"[{msg['role'].upper()}] > {msg['content']}")

# 5. Entrada de comandos del usuario
prompt = st.chat_input("Ingresa un comando o pregunta...")

if prompt:
    st.session_state.historial.append({"role": "user", "content": prompt})
    
    # Invocación real del grafo de LangGraph
    eventos = app_graph.stream(
        {"messages": [HumanMessage(content=prompt)]}, 
        config, 
        stream_mode="values"
    )
    
    respuesta_final = ""
    for evento in eventos:
        ultimo_mensaje = evento["messages"][-1]
        
        # Mostrar las herramientas ejecutadas en el log del sistema
        if getattr(ultimo_mensaje, 'tool_calls', None):
            for tc in ultimo_mensaje.tool_calls:
                st.session_state.historial.append({"role": "sys", "content": f"Ejecutando proceso interno: {tc['name']}"})
        
        # Capturar la última respuesta de la IA
        if ultimo_mensaje.type == "ai" and ultimo_mensaje.content:
            respuesta_final = ultimo_mensaje.content
            
    if respuesta_final:
        st.session_state.historial.append({"role": "novasync", "content": respuesta_final})
        
    st.rerun()
