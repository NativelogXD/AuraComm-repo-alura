<p align="center">
  <img src="https://img.shields.io/badge/version-1.5.0-00FF41?style=for-the-badge&labelColor=050505" alt="version"/>
  <img src="https://img.shields.io/badge/python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="python"/>
  <img src="https://img.shields.io/badge/docker-ready-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="docker"/>
  <img src="https://img.shields.io/badge/license-MIT-yellow?style=for-the-badge" alt="license"/>
</p>

<h1 align="center">🛰️ AuraComm v1.5 — NovaSync Solutions</h1>
<h3 align="center">Agente de Inteligencia Artificial Corporativo B2B · Telecomunicaciones & Infraestructura de Red</h3>

<p align="center">
  <em>Arquitectura Cloud-Native · Determinista · Alta Seguridad · Anti-Alucinaciones</em>
</p>

---

## 📋 Descripción

**AuraComm** es el núcleo cognitivo de **NovaSync Solutions**, una corporación simulada del sector de Telecomunicaciones e Infraestructura de Red B2B. Este repositorio contiene el código fuente de un agente de IA corporativo diseñado con una arquitectura **Cloud-Native, Determinista y de Alta Seguridad**.

El agente asiste a gerentes, ejecutivos de finanzas y analistas de red, resolviendo consultas complejas sobre:
- 📊 **Infraestructura de telefonía y métricas de negocio (KPIs)**
- 💰 **Facturación y análisis de ingresos**
- 📜 **Niveles de servicio (SLA) y políticas corporativas**
- 🔧 **Auditorías de hardware y troubleshooting**
- 🔐 **Privacidad de datos y cumplimiento**

Todo mediante bases de datos corporativas centralizadas en un **Data Lake en la nube**.

---

## 🏗️ Arquitectura de la Solución

A diferencia de los chatbots convencionales, AuraComm emplea un diseño **determinista** que mitiga las alucinaciones de datos mediante un orquestador que sigue estrictas reglas de negocio.

```
┌──────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Streamlit)                      │
│                   UI Tipo Terminal · CSS Custom                  │
└─────────────────────────────┬────────────────────────────────────┘
                              │
┌─────────────────────────────▼────────────────────────────────────┐
│               CEREBRO ORQUESTADOR (LangGraph)                    │
│          Gemini 3.1 Flash Lite · System Prompt B2B               │
│         Guardrails · Query Expansion · ReAct Pattern             │
├──────────────────┬───────────────────────────────────────────────┤
│                  │              │                                 │
│    ┌─────────────▼──────┐ ┌────▼────────────────────┐           │
│    │  TOOL: KPI Engine  │ │  TOOL: RAG Pipeline     │           │
│    │  Capa Semántica    │ │  Sub-Agente Lector      │           │
│    │  Pandas + JSON     │ │  Groq (Llama 3.1 8B)   │           │
│    │  metrics_catalog   │ │  FAISS + MMR Retrieval  │           │
│    └────────┬───────────┘ └────────┬────────────────┘           │
│             │                      │                             │
│    ┌────────▼───────────┐ ┌────────▼────────────────┐           │
│    │  DATA LAKE (S3)    │ │  VECTORSTORE (FAISS)    │           │
│    │  MinIO · Boto3     │ │  HuggingFace Embeddings │           │
│    │  Client.csv        │ │  paraphrase-MiniLM-L12  │           │
│    │  Record.csv        │ │  PDFs Corporativos      │           │
│    └────────────────────┘ └─────────────────────────┘           │
│                                                                  │
│    ┌─────────────────────────────────────────────────┐          │
│    │  MEMORIA PERSISTENTE (SQLite + LangGraph)       │          │
│    │  Checkpointer · Thread-safe · Volumen Docker    │          │
│    └─────────────────────────────────────────────────┘          │
└──────────────────────────────────────────────────────────────────┘
```

### Capas de Inteligencia

| Capa | Tecnología | Función |
|------|-----------|---------|
| 🧠 **Cerebro Orquestador** | Gemini 3.1 Flash Lite (Google) | Agente principal. Analiza intención, aplica Query Expansion, invoca herramientas, verifica Guardrails y ensambla respuestas B2B |
| 📖 **Sub-Agente RAG** | Llama 3.1 8B (Groq) | Especializado en extracción de texto de documentos recuperados del índice vectorial. Devuelve JSON estructurado |
| 🔢 **Motor de Embeddings** | paraphrase-multilingual-MiniLM-L12-v2 (HuggingFace) | Vectorización local de documentos. Independiente de APIs externas. Soporte multilingüe (español/inglés) |
| 🗄️ **Data Lake** | MinIO (S3-Compatible) + Boto3/S3fs | Fuente de verdad en la nube. CSVs y PDFs corporativos. Procesamiento Stateless in-memory |

---

## 🛠️ Stack Tecnológico Completo

### 🤖 Inteligencia Artificial y LLMs

| Tecnología | Versión | Uso |
|-----------|---------|-----|
| **LangChain** | 1.3.11 | Framework de orquestación de LLMs, cadenas LCEL, prompts y parsers |
| **LangGraph** | 1.2.8 | Máquina de estados finita para el flujo agentivo (ReAct Pattern) |
| **LangGraph Checkpoint SQLite** | 3.1.0 | Persistencia de memoria conversacional entre sesiones |
| **LangGraph Prebuilt** | 1.1.0 | `ToolNode` prebuilts para ejecución de herramientas |
| **LangChain Google GenAI** | 4.2.7 | Integración con la API de Google Gemini |
| **LangChain Groq** | 1.1.3 | Integración con la API de Groq (inferencia ultrarrápida) |
| **LangChain HuggingFace** | 1.2.2 | Embeddings locales vía HuggingFace |
| **LangChain Community** | 0.4.2 | VectorStores (FAISS) y utilidades comunitarias |
| **LangSmith** | 0.10.0 | Observabilidad, trazas y debugging de cadenas LLM en producción |

### 🔍 Búsqueda Vectorial y RAG

| Tecnología | Versión | Uso |
|-----------|---------|-----|
| **FAISS (CPU)** | 1.14.3 | Base de datos vectorial de Facebook AI para búsqueda por similaridad |
| **Sentence Transformers** | 5.6.0 | Framework para modelos de embeddings semánticos |
| **Transformers** | 5.13.0 | Biblioteca de HuggingFace para modelos de lenguaje pre-entrenados |
| **Tokenizers** | 0.22.2 | Tokenización rápida en Rust para modelos Transformer |
| **PyTorch (CPU)** | latest | Backend de cómputo para modelos de embeddings (versión CPU optimizada) |
| **LangChain Text Splitters** | 1.1.2 | `RecursiveCharacterTextSplitter` para fragmentación semántica de documentos |
| **PyPDF** | 6.14.2 | Extracción de texto desde PDFs corporativos directamente en memoria |

### 📊 Procesamiento y Análisis de Datos

| Tecnología | Versión | Uso |
|-----------|---------|-----|
| **Pandas** | 3.0.3 | Motor de análisis tabular. Ejecuta KPIs (conteo, promedio, suma, correlación, percentiles) |
| **Pydantic** | 2.13.4 | Validación estricta de esquemas de entrada/salida. Guardrails de tipo |

### ☁️ Cloud, Storage y Data Lake

| Tecnología | Versión | Uso |
|-----------|---------|-----|
| **Boto3** | latest | SDK de AWS/S3 para conexión con MinIO (Data Lake) |
| **S3fs** | latest | Filesystem virtual S3 para lectura directa de CSVs con Pandas |
| **MinIO** | (servidor) | Object Storage S3-compatible. Data Lake corporativo en la nube |

### 🖥️ Frontend y UI

| Tecnología | Versión | Uso |
|-----------|---------|-----|
| **Streamlit** | 1.59.2 | Framework web para la interfaz de usuario tipo terminal retro |
| **CSS Custom** | — | Inyección de estilos para simular consola corporativa (fondo negro, texto verde neón) |
| **Arte ASCII** | — | Branding visual de NovaSync en la interfaz |

### 🐳 Infraestructura y DevOps

| Tecnología | Versión | Uso |
|-----------|---------|-----|
| **Docker** | — | Contenedorización de la aplicación. Imagen `python:3.11-slim` |
| **Docker Compose** | 3.8 | Orquestación de servicios con variables de entorno y volúmenes |
| **Healthcheck** | — | Monitoreo de salud del contenedor vía `curl` al endpoint de Streamlit |
| **Volúmenes Persistentes** | — | Persistencia de base SQLite e índices FAISS entre reinicios |

### 🔧 Utilidades y Runtime

| Tecnología | Versión | Uso |
|-----------|---------|-----|
| **Python** | 3.11 | Runtime principal |
| **python-dotenv** | 1.2.2 | Carga de variables de entorno desde `.env` |
| **SQLite3** | (stdlib) | Base de datos para checkpoints de memoria conversacional |
| **hashlib/MD5** | (stdlib) | Sistema de ETags para invalidación inteligente del índice FAISS |
| **asyncio** | (stdlib) | Manejo de loops asíncronos y parches para Windows (WinError 10054) |
| **logging** | (stdlib) | Logging estructurado con timestamps para telemetría |
| **uuid** | (stdlib) | Generación de IDs únicos por sesión de navegador |
| **re** | (stdlib) | Sanitización de texto extraído de PDFs (regex) |

### 📡 Plataformas de Despliegue Compatibles

| Plataforma | Tipo |
|-----------|------|
| **Dokploy** | PaaS Self-Hosted |
| **Coolify** | PaaS Self-Hosted |
| **Servidores On-Premise** | Bare Metal / VPS |
| **Cualquier host Docker** | IaaS |

---

## 🔒 Sistema de Seguridad (Guardrails)

AuraComm implementa múltiples capas de protección anti-alucinaciones:

1. **Guardrail de Dominio:** System Prompt estricto que rechaza consultas fuera del dominio B2B de NovaSync.
2. **Guardrail de Esquema (Pydantic):** Validación en tiempo real de nombres de métricas contra `metrics_catalog.json`. Si la métrica no existe, Pydantic lanza error antes de que el LLM pueda alucinar.
3. **Guardrail Anti-Invención (RAG):** El sub-agente marca `es_informacion_inventada: true` si el dato no está explícitamente en el contexto. El sistema bloquea la respuesta alucinada.
4. **Guardrail de Premisas Falsas:** Si la pregunta asume algo incorrecto, el agente desmiente la premisa citando la política real.
5. **Guardrail de API (Resiliencia):** Captura y traduce errores HTTP (503, 429, 413, 404, 400) a mensajes amigables sin exponer stack traces.
6. **Capa Semántica Declarativa:** Motor de ejecución basado en metadatos JSON. Imposible ejecutar código arbitrario (protección contra RCE).
7. **Query Expansion:** El esquema `ConsultaPDFInput` obliga al LLM a expandir la consulta con sinónimos técnicos en inglés y español antes de buscar en FAISS.

---

## ⚙️ Configuración y Ejecución Local

### 1. Clonar e Instalar

```bash
git clone <url-del-repositorio>
cd AuraComm/src

# Crear y activar entorno virtual
python -m venv .venv
.\.venv\Scripts\activate     # Windows
# source .venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configurar el Entorno (.env)

En el directorio `src/`, crea un archivo `.env` con las siguientes variables:

```env
# ═══════════════════════════════════════════
# CEREBRO B2B PRINCIPAL (Orquestador)
# ═══════════════════════════════════════════
GEMINI_API_KEY=tu_clave_gemini_aqui

# ═══════════════════════════════════════════
# SUB-AGENTE RAG (Extracción Rápida de Texto)
# ═══════════════════════════════════════════
GROQ_API_KEY=gsk_tu_clave_groq_aqui

# ═══════════════════════════════════════════
# DATA LAKE (MinIO / S3-Compatible)
# ═══════════════════════════════════════════
MINIO_ENDPOINT=tu_endpoint_minio
MINIO_ROOT_USER=tu_usuario
MINIO_ROOT_PASSWORD=tu_contraseña
MINIO_BUCKET_NAME=tu_bucket

# ═══════════════════════════════════════════
# OBSERVABILIDAD (Opcional - LangSmith)
# ═══════════════════════════════════════════
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=tu_clave_langsmith
LANGCHAIN_PROJECT=AuraComm_Produccion
```

### 3. Iniciar el Agente

```bash
python -m streamlit run main.py
```

> **Nota:** La primera ejecución tomará tiempo adicional mientras se descarga el modelo de embeddings de HuggingFace (`paraphrase-multilingual-MiniLM-L12-v2`) y se construye el índice vectorial FAISS desde el Data Lake S3.

---

## 🐳 Despliegue en Producción (Docker)

El proyecto incluye un `Dockerfile` optimizado (multi-stage caching) y un `docker-compose.yml` listo para despliegue:

```bash
# Construir e iniciar
docker-compose up -d --build
```

### Características del contenedor:
- **Imagen base:** `python:3.11-slim` (ligera, ~150MB)
- **Healthcheck integrado:** Monitoreo automático cada 30s vía `/_stcore/health`
- **Volúmenes persistentes:** `/app/db` para SQLite y caché de FAISS
- **Variables inyectables:** Todas las credenciales via `environment` en Docker Compose
- **Start period:** 60s para permitir la carga inicial de embeddings

---

## 📁 Estructura del Proyecto

```
AuraComm/
├── .streamlit/
│   └── config.toml              # Tema visual (terminal verde/negro)
├── src/
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── guardrails.py        # Manejo de errores de API (503, 429, etc.)
│   │   ├── orcuestrator.py      # Grafo LangGraph (StateGraph + ToolNode)
│   │   ├── schemas.py           # Pydantic schemas (entrada/salida)
│   │   └── tools.py             # Herramientas del agente (KPI + RAG)
│   ├── core/
│   │   ├── __init__.py
│   │   └── setup_env.py         # Bootstrap: carga S3, FAISS, DataFrames
│   ├── data/
│   │   ├── __init__.py
│   │   ├── data_cleaning.py     # ETL: lectura y limpieza de CSVs desde MinIO
│   │   ├── metrics_catalog.json # Catálogo declarativo de 22 KPIs
│   │   └── semantic_layer.py    # Motor de ejecución de métricas (Pandas)
│   ├── rag/
│   │   ├── models.py            # Configuración de LLMs (Gemini, Groq, Embeddings)
│   │   └── rag.py               # Pipeline RAG completo (S3 → PDF → FAISS)
│   ├── main.py                  # Punto de entrada Streamlit
│   ├── requirements.txt         # 41 dependencias Python
│   └── .env                     # Variables de entorno (no versionado)
├── Dockerfile                   # Imagen Docker optimizada
├── docker-compose.yml           # Orquestación de servicios
├── ARQUITECTURA.md              # Documentación técnica detallada
└── README.md                    # Este archivo
```

---

## 🔬 Catálogo de KPIs Disponibles (22 Métricas)

El motor semántico ejecuta operaciones matemáticas de forma **determinista** sobre los DataFrames. Las operaciones soportadas son:

| Operación | Descripción |
|----------|-------------|
| `conteo` | Conteo de registros filtrados |
| `promedio` | Media aritmética de una columna |
| `suma` | Suma total de una columna |
| `maximo` | Valor máximo de una columna |
| `valor_exacto` | Valor puntual de un registro |
| `argmax` | ID del registro con valor máximo |
| `group_by_max` | Agrupación + categoría con mayor promedio |
| `correlacion_pearson` | Coeficiente de correlación entre dos variables |
| `percentil_75_promedio` | Promedio del cuartil superior (P75) |

Todas las métricas soportan **filtros dinámicos** con operadores: `==`, `>`, `<`, `>=`, `<=`, `!=`.

---

## 💬 Ejemplos de Interacción

```text
(Analisis de Documentos RAG).
¿Bajo que circunstancias especificas un cliente tiene derecho a recibir creditos de servicio proporcionales segun el SLA de NovaSync?" 


(Uso de Query Expansion).
"¿Que par de variables se utilizan para contabilizar y gestionar la cantidad de sub-dispositivos fisicos o equipos registrados asociados a un mismo tenant?" 


(Listado dinamico desde el catalogo semantico de metricas).


"¿Que kpis manejas?" (Listado dinamico desde el catalogo semantico de metricas).


(Analisis tabular).
"¿Cuantos clientes cancelaron su suscripcion este mes y cual era su ingreso promedio?" 


(Comprension RAG Avanzada).
"Si detectan que mi tenant esta recibiendo limitacion de ancho de banda (throttling), ¿que variables en el panel de telemetria confirmarian que estoy violando la politica de Fair Use mediante rafagas automatizadas?" 


 (Capa Semantica - Agrupaciones)
"¿Cual es el promedio de caidas de voz mensuales comparando a los clientes activos con los que cancelaron su servicio?"


(Capa Semantica - Filtros)
."¿Cual es la suma total de ingresos generados exclusivamente por los clientes en el area de 'CHICAGO AREA'?" .


(Capa Semantica - Operaciones Complejas).
"¿Existe una correlacion estadistica fuerte entre la antiguedad de los equipos y la decision de cancelar el servicio?" 


(Capa Semantica - Percentiles).
"¿Cual es el promedio de interacciones con servicio al cliente del 25% de clientes que mas ingresos generan?" 

```

---

## 📝 Changelog

### v1.5.0 (2026-07-25)
- 📖 README completamente reescrito con documentación exhaustiva de todo el stack tecnológico
- 📊 22 KPIs documentados en el catálogo semántico
- 🔒 7 capas de Guardrails documentadas
- 🏗️ Diagrama de arquitectura actualizado
- 📁 Estructura de proyecto documentada

### v1.0.0
- 🚀 Release inicial
- 🧠 Arquitectura multi-modelo (Gemini + Groq + HuggingFace)
- 🔍 Pipeline RAG con FAISS + MMR
- 📊 Capa Semántica declarativa con `metrics_catalog.json`
- 🐳 Dockerización completa con Healthcheck
- ☁️ Integración con Data Lake MinIO/S3

---

## 📄 Licencia

Este proyecto fue desarrollado como proyecto final del programa de formación **Alura LATAM**.

---

<p align="center">
  <strong>NovaSync Solutions</strong> · <em>Infraestructura Inteligente B2B</em><br/>
  <code>AuraComm v1.5.0 Enterprise</code>
</p>
