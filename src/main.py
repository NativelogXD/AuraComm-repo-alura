import streamlit as st
import sys
import os
import asyncio
import logging

# Forzar codificación UTF-8 para evitar errores de consola en Windows (charmap)
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Configuración global de logging estructurado
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Parche para silenciar el inofensivo pero ruidoso ConnectionResetError (WinError 10054) en Windows
if sys.platform.startswith("win"):
    try:
        from functools import wraps
        from asyncio.proactor_events import _ProactorBasePipeTransport
        def silence_winerror_10054(func):
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                try:
                    return func(self, *args, **kwargs)
                except ConnectionResetError:
                    pass
            return wrapper
        _ProactorBasePipeTransport._call_connection_lost = silence_winerror_10054(_ProactorBasePipeTransport._call_connection_lost)
    except ImportError:
        pass

from langchain_core.messages import HumanMessage
from core.setup_env import SetupEnvironment
from agent.tools import HerramientasFactory
from agent.orcuestrator import crear_orquestador, limpiar_historial
import langchain

# Deshabilitar logs verbosos de LangChain en producción
langchain.debug = False

# 1. Configuración básica de la página
st.set_page_config(page_title="Terminal NovaSync", layout="wide")

# Separamos la carga pesada (DataFrames, Modelos) del grafo
@st.cache_resource(show_spinner=False)
def cargar_datos():
    return SetupEnvironment.inicializar()

import uuid

# Cargamos los datos cacheados
df_client, df_record = cargar_datos()

# Anti-Patrón #5: Validación explícita de conexión al Data Lake
if df_client is None or df_record is None:
    st.error("⚠️ ERROR CRÍTICO: No se pudo conectar al Data Lake (MinIO). Verifica las credenciales en las variables de entorno de Dokploy.")
    st.stop()

# Inicializamos el grafo en tiempo real para no atrapar herramientas obsoletas en caché
factory = HerramientasFactory(df_client, df_record)
app_graph = crear_orquestador(factory.obtener_tools())

# Generar un thread_id único por sesión de navegador para no arrastrar la memoria vieja
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

config = {"configurable": {"thread_id": st.session_state.thread_id}}

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

# Botón lateral para limpiar historial manualmente (muy útil para depurar)
with st.sidebar:
    st.markdown("### ⚙️ Panel de Control")
    if st.button("🗑️ Limpiar Historial"):
        limpiar_historial()
        st.cache_resource.clear()
        st.session_state.clear()
        st.rerun()

if prompt:
    # 5.1 Intercepción de comandos del sistema
    if prompt.strip().lower() in ["clear", "reset", "/clear", "/reset"]:
        limpiar_historial()
        st.cache_resource.clear()
        st.session_state.clear()
        st.rerun()
        
    st.session_state.historial.append({"role": "user", "content": prompt})
    
    # Invocación real del grafo de LangGraph
    respuesta_final = ""
    
    with st.status("Analizando solicitud...", expanded=True) as status:
        eventos = app_graph.stream(
            {"messages": [HumanMessage(content=prompt)]}, 
            config, 
            stream_mode="values"
        )
        
        for evento in eventos:
            ultimo_mensaje = evento["messages"][-1]
            
            # Mostrar las herramientas ejecutadas en el log del sistema (telemetría en vivo)
            if getattr(ultimo_mensaje, 'tool_calls', None):
                for tc in ultimo_mensaje.tool_calls:
                    msg = f"Ejecutando proceso interno: {tc['name']}..."
                    status.write(f"⚙️ {msg}")
                    st.session_state.historial.append({"role": "sys", "content": msg})
            
            # Capturar la última respuesta de la IA
            if ultimo_mensaje.type == "ai" and ultimo_mensaje.content:
                respuesta_final = ultimo_mensaje.content
                status.update(label="Análisis completado", state="complete", expanded=False)
                
    if respuesta_final:
        st.session_state.historial.append({"role": "novasync", "content": respuesta_final})
        
    st.rerun()
