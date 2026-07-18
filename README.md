# NovaSync: Agente Digital B2B (Arquitectura Determinista y Cloud-Native)

## Descripción General del Proyecto

**NovaSync B2B** es un agente de inteligencia artificial corporativo diseñado para interactuar con gerentes y clientes empresariales. La corporación simulada opera en el sector de **Telecomunicaciones e Infraestructura de Red B2B** (proveyendo telefonía, venta de equipos de red, monitoreo de latencia/uptime y servicios MRR).

El agente tiene acceso seguro a bases de datos corporativas en la nube (documentos PDF de arquitectura/soporte y bases de datos tabulares de clientes de telefonía alojadas en un Data Lake) para resolver consultas complejas en tiempo real a través de una interfaz web estilo terminal.

A diferencia de los chatbots tradicionales, este proyecto emplea una **Arquitectura Determinista y Cloud-Native**. Esto significa que las herramientas, las conexiones a bases de datos y los formatos de salida están estrictamente controlados mediante validación estructurada y protocolos seguros en la nube, impidiendo que el LLM alucine datos corporativos.

---

## Arquitectura de la Solución

El núcleo del sistema está construido sobre un grafo de estados (**StateGraph**) que orquesta el razonamiento de la IA, expuesto mediante una interfaz web asíncrona:

1. **Frontend Web (Streamlit)**: Interfaz inmersiva estilo "Terminal Cyberpunk" (CSS Inyectado) que proporciona una experiencia fluida al usuario final. La arquitectura asegura que los motores de IA y conexiones de nube carguen mediante un patrón *Singleton* en memoria caché para evitar latencias en la navegación.
2. **Orquestador (LangGraph)**: Controla el flujo cognitivo del agente. Permite mantener el historial conversacional persistente mediante SQLite y tomar decisiones de enrutamiento automáticas.
3. **Integración Cloud (Data Lake)**: Toda la información de la empresa vive centralizada en un Bucket S3 (MinIO). La aplicación local actúa únicamente como procesador de esta información remota.
4. **Sistema RAG Open-Source (Local Embeddings)**:
   - Se conecta al Bucket mediante `boto3`, escanea la nube y descarga temporalmente los documentos `.pdf` a la memoria RAM (flujo *stateless*).
   - Utiliza **HuggingFace Embeddings** (`all-MiniLM-L6-v2`) de forma local para indexar vectores. Esto garantiza 100% de independencia de límites de cuota de APIs de terceros (como Google/OpenAI) para la recuperación de documentos.
   - Cuenta con un sistema de **Sincronización Inteligente de ETags (MD5)** que detecta automáticamente si los PDFs fueron modificados en la nube para reconstruir el índice vectorial (FAISS) solo cuando es estrictamente necesario, ahorrando recursos de CPU.
5. **Análisis Estructurado de Datos (CSV en Streaming)**: En lugar de descargar grandes volúmenes de datos al disco, utiliza Pandas integrado con `s3fs` para procesar los registros tabulares directo desde la nube a la memoria, ejecutando código dinámico generado por la IA con validaciones de seguridad sintáctica.
6. **Dockerización PaaS**: Preparado con un `Dockerfile` optimizado (imagen `python:3.10-slim`) y gestión de volúmenes persistentes (`DB_DIR`), listo para despliegues con cero configuración (Zero-Config) en plataformas modernas como **Coolify** o **Dokploy**.

---

## Tecnologías y Herramientas Utilizadas

- **Lenguaje**: Python 3.10+
- **Frontend**: Streamlit
- **Orquestación IA**: LangChain & LangGraph
- **Motor Cognitivo (LLM)**: Groq (Llama 3.1 8B Instant)
- **Motor de Embeddings**: HuggingFace (`all-MiniLM-L6-v2` vía `sentence-transformers`)
- **Base de Datos Vectorial**: FAISS (Facebook AI Similarity Search)
- **Data Lake (Cloud Storage)**: MinIO (Compatible 100% con Amazon S3)
- **Conectores S3**: Boto3 & S3fs
- **Procesamiento Tabular**: Pandas
- **Infraestructura**: Docker

---

## Estructura del Proyecto

La fuente de verdad de los datos es tu **Bucket de MinIO**. Debes asegurarte de que tus archivos `Client.csv`, `Record.csv` y los PDFs corporativos estén subidos dentro de una carpeta llamada `data/` en la raíz de tu bucket en la nube.

```text
📁 AuraComm
├── 📄 Dockerfile        # Receta de despliegue en contenedores.
├── 📄 README.md
└── 📁 src
    ├── 📁 agent         # Lógica del orquestador, tools y esquemas de Pydantic.
    ├── 📁 core          # Configuración inicial y variables de entorno.
    ├── 📁 excepciones   # Gestor de errores y límites de cuota (Rate Limits).
    ├── 📁 rag           # Modelos RAG, Embeddings locales y FAISS.
    ├── 📄 main.py       # Interfaz web de Streamlit (Punto de entrada).
    └── 📄 requirements.txt
```

---

## Instrucciones de Ejecución Local (Desarrollo)

1. **Clonar y Preparar el Entorno:**
   ```bash
   cd src/
   ```

2. **Instalar Dependencias:**
   Se recomienda usar un entorno virtual (`.venv`).
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar Variables de Entorno:**
   Crea un archivo `.env` en la carpeta `src/` con tus claves (Ya NO se necesita API de Gemini para embeddings):

   ```env
   # Cerebro Cognitivo LLM
   GROQ_API_KEY=gsk_tu_clave_aqui

   # Configuración de Nube S3 (MinIO Data Lake)
   MINIO_ENDPOINT=http://tu-enlace-de-minio-puerto-9000
   MINIO_ACCESS_KEY=tu_usuario
   MINIO_SECRET_KEY=tu_contraseña
   MINIO_BUCKET_NAME=nombre_de_tu_bucket

   # Trazabilidad y Monitoreo (LangSmith)
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
   LANGCHAIN_API_KEY=ls__tu_clave_aqui
   LANGCHAIN_PROJECT=AuraComm_Digital_Produccion
   ```

4. **Ejecutar el Frontend Web:**
   ```bash
   python -m streamlit run main.py
   ```
   *Nota: La primera ejecución tomará entre 1 y 2 minutos extra mientras descarga el modelo matemático de HuggingFace (~90MB) y construye el índice vectorial inicial.*

---

## Despliegue en Producción (Coolify / Dokploy)

El proyecto está diseñado para desplegarse mediante Docker. Al conectar tu repositorio de GitHub a tu plataforma PaaS:
1. Configura el puerto expuesto del contenedor a **8501**.
2. Inyecta todas las variables de entorno de arriba directamente en el panel de control de tu PaaS.
3. Monta un Volumen persistente en la ruta `/app/db` dentro del contenedor. Esto asegurará que la memoria de LangGraph y los índices de FAISS no se pierdan al reiniciar la aplicación.

---

## Ejemplos de Preguntas (Pruebas)

- *"Háblame acerca del documento DOC-ARCH-001 y de qué trata."* (Consulta RAG)
- *"¿Cuáles son las políticas de privacidad según el documento DOC-PRIV-003?"* (Consulta RAG)
- *"Calcula cuál es la cantidad total de clientes en la base de datos."* (Consulta CSV Analítica)
- *"¿Cuántos clientes en el archivo Record.csv experimentaron fallas en las llamadas?"* (Consulta CSV Analítica)
- *"Cuéntame un chiste."* (El orquestador bloqueará esta solicitud, demostrando el límite estricto de dominio B2B).
