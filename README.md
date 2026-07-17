# NovaSync: Agente Digital B2B (Arquitectura Determinista y Cloud-Native)

## Descripción General del Proyecto

**NovaSync B2B** es un agente de inteligencia artificial corporativo diseñado para interactuar con gerentes y clientes empresariales. La corporación simulada opera en el sector de **Telecomunicaciones e Infraestructura de Red B2B** (proveyendo telefonía, venta de equipos de red, monitoreo de latencia/uptime y servicios MRR).

El agente tiene acceso seguro a bases de datos corporativas en la nube (documentos PDF de arquitectura/soporte y bases de datos tabulares de clientes de telefonía alojadas en un Data Lake) para resolver consultas complejas en tiempo real.

A diferencia de los chatbots tradicionales, este proyecto emplea una **Arquitectura Determinista y Cloud-Native**. Esto significa que las herramientas, las conexiones a bases de datos y los formatos de salida están estrictamente controlados mediante validación estructurada y protocolos seguros en la nube, impidiendo que el LLM alucine datos corporativos.

---

## Arquitectura de la Solución

El núcleo del sistema está construido sobre un grafo de estados (**StateGraph**) que orquesta el razonamiento de la IA:

1. **Orquestador (LangGraph)**: Controla el flujo cognitivo del agente. Permite mantener el historial conversacional (Memoria) y tomar decisiones de enrutamiento (ej. saber cuándo usar una herramienta y cuándo responder al usuario).
2. **Integración Cloud (Data Lake)**: Toda la información de la empresa vive centralizada en un Bucket S3 (MinIO). La aplicación local actúa únicamente como procesador de esta información remota.
3. **Sistema RAG Optimizado y Selectivo**:
   - Se conecta al Bucket mediante `boto3`, escanea la nube y descarga temporalmente solo los documentos `.pdf` de interés, ignorando archivos masivos (como CSVs).
   - Procesa los PDFs y los almacena en un índice vectorial local (**FAISS**).
   - Utiliza `MultiQueryRetriever` con recuperación controlada (`k=2`) para evitar sobrecargar la ventana de contexto de los LLM.
   - Cuenta con un sistema de **Sincronización Inteligente de ETags** que detecta automáticamente si los PDFs fueron modificados en la nube para reconstruir los embeddings solo cuando es estrictamente necesario, ahorrando recursos.
4. **Análisis Estructurado de Datos (CSV en Streaming)**: En lugar de descargar grandes volúmenes de datos al disco, utiliza Pandas integrado con `s3fs` para transmitir los registros tabulares directo desde la nube a la memoria RAM, filtrándolos bajo estrictos esquemas de Pydantic.
5. **Human-in-the-Loop (HITL)**: Implementa una capa de seguridad donde cualquier ejecución de herramientas internas (lectura de PDFs, acceso a bases de datos, borrado o modificación) queda pausada a la espera de **aprobación manual del administrador**.
6. **Interceptador Anti-Alucinaciones XML**: Un parche de ingeniería (Regex Parser) a nivel de orquestador que intercepta las fugas de formato del LLM y las convierte internamente en la API estructurada nativa de LangChain.

---

## Tecnologías y Herramientas Utilizadas

- **Lenguaje**: Python 3.10+
- **Orquestación IA**: LangChain & LangGraph
- **Modelos de Lenguaje (LLM)**: Groq (Llama 3.1 8B Instant) / Gemini 2.5 Flash
- **Modelos de Embeddings**: HuggingFace (`intfloat/multilingual-e5-small`)
- **Base de Datos Vectorial**: FAISS (Facebook AI Similarity Search)
- **Data Lake (Cloud Storage)**: MinIO (Compatible 100% con Amazon S3)
- **Conectores S3**: Boto3 & S3fs
- **Procesamiento de Datos Tabulares**: Pandas
- **Validación Estructurada**: Pydantic
- **Base de Datos de Memoria**: SQLite (`checkpoints_auracomm.db`)

---

## Estructura del Proyecto

Para que el sistema funcione correctamente, la fuente de verdad ya no es tu disco local, sino tu **Bucket de MinIO**. Debes asegurarte de que tus archivos `Client.csv`, `Record.csv` y los PDFs corporativos estén subidos dentro de una carpeta llamada `data/` en la raíz de tu bucket en la nube.

```text
📁 AuraComm
├── 📄 README.md
└── 📁 src
    ├── 📁 agent         # Lógica del orquestador, tools y esquemas de Pydantic.
    ├── 📁 core          # Configuración inicial y arranque de la aplicación.
    ├── 📁 excepciones   # Gestor de errores y límites de cuota (Rate Limits).
    ├── 📁 rag           # Modelos RAG, Embeddings, conexión a Boto3 y orquestación FAISS.
    ├── 📁 ui            # Interfaz CLI con pausa de seguridad (Human-in-the-Loop).
    ├── 📄 main.py       # Punto de entrada principal.
    └── 📄 requirements.txt
```

---

## Instrucciones de Instalación y Ejecución

1. **Clonar y Preparar el Entorno:**
   Asegúrate de estar en el directorio `src/` del proyecto.

   ```bash
   cd src/
   ```

2. **Instalar Dependencias:**
   Se recomienda usar un entorno virtual (`.venv`).

   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar Variables de Entorno:**
   Asegúrate de tener un archivo `.env` en la carpeta `src/` con tus claves de API, configuración de MinIO y trazabilidad:

   ```env
   # Modelos LLM y Embeddings
   GROQ_API_KEY=gsk_tu_clave_aqui
   GEMINI_API_KEY=AIzaSy_tu_clave_aqui

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

4. **Ejecutar el Agente:**

   ```bash
   python main.py
   ```

   *La primera ejecución tomará unos segundos extra mientras se conecta a MinIO, descarga temporalmente los PDFs y construye el índice FAISS inicial.*

---

## Ejemplos de Preguntas

- *"Háblame acerca del documento DOC-ARCH-001 y de qué trata."* (Consulta RAG)
- *"¿Cuáles son las políticas de privacidad según el documento DOC-PRIV-003?"* (Consulta RAG)
- *"Calcula cuál es la cantidad total de clientes en la base de datos."* (Consulta CSV Analítica)
- *"¿Cuántos clientes en el archivo Record.csv experimentaron fallas en las llamadas?"* (Consulta CSV Analítica)
- *"Cuéntame un chiste."* (Para probar el escudo anti-prompting fuera de dominio)

## Ejemplos de Respuestas

**Consulta Analítica:** *"Calcula cuál es la cantidad total de clientes en la base de datos."*

**Salida en consola:**

```text
[⚠️ ALERTA HITL]: El agente solicita ejecutar una herramienta interna.
 -> Herramienta: analizar_datos_csv
 -> Argumentos: {'consulta': 'cantidad total de clientes en la base de datos'}
¿Aprobar ejecución? (s = sí / n = no): s
[✔️ Aprobado. Procesando...]

[🤖 AuraComm]: Contamos con un total de 100,000 clientes corporativos registrados en nuestra base de datos actual.
```

**Consulta (Fuera de dominio):** *"Escribe un poema sobre el mar."*

**Salida en consola:**

```text
[🤖 AuraComm]: Lo siento, soy un agente corporativo exclusivo de NovaSync. Solo estoy autorizado para asistir en temas relacionados con nuestros servicios, políticas técnicas y bases de clientes B2B. ¿En qué te puedo ayudar respecto a la corporación?
```

---

## Advertencias y Recomendaciones (API Limits)

Este proyecto está diseñado para funcionar en un entorno de capa gratuita (Free Tier), por lo que se deben tener en cuenta las siguientes protecciones implementadas:

1. **Límites de Tokens por Minuto (Groq TPM)**:
   - Los modelos gratuitos de Groq tienen un límite estricto de **6000 Tokens Por Minuto (TPM)**.
   - **Solución implementada:** Para evitar que el historial conversacional crezca infinitamente y rompa este límite, el orquestador tiene un **Recortador de Memoria a Corto Plazo** que solo envía los últimos 5 mensajes al LLM. Además, el RAG fue capado a `k=2` fragmentos para aligerar el payload.

2. **Ráfagas de Peticiones (Rate Limits)**:
   - Si decides cambiar el motor en `models.py` para usar **Google Gemini 2.5 Flash**, ten en cuenta que la API gratuita solo permite **15 peticiones por minuto**. Dado que LangGraph hace peticiones múltiples por cada interacción (decidir herramienta -> ejecutar -> responder), hacer dos preguntas muy rápido causará un error `429 RESOURCE_EXHAUSTED`.
   - **Recomendación:** Espera ~15 segundos entre preguntas si usas la API de Gemini, o mantén el código actual con **Llama 3.1 8B en Groq**, el cual ofrece una cuota generosa ideal para evaluaciones y testing ininterrumpido.

3. **Memoria (Checkpoints)**:
   - Si la terminal falla inesperadamente por cuotas excedidas, se recomienda limpiar el caché de memoria eliminando el archivo `checkpoints_auracomm.db` y reiniciar el script.
