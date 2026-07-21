# Arquitectura y Flujo de Ejecución de NovaSync (AuraComm)

## 1. Contexto General del Proyecto (¿Qué hace?)

**NovaSync B2B (AuraComm)** es un agente de Inteligencia Artificial de grado corporativo diseñado específicamente para el sector de Telecomunicaciones e Infraestructura de Red B2B. 

Su propósito principal es servir como un asistente determinista para gerentes y analistas que requieren respuestas instantáneas y precisas basadas en datos internos de la compañía. En lugar de ser un simple chatbot de "charla", NovaSync es una herramienta analítica estricta que:
1. Responde preguntas sobre métricas de negocio (KPIs) como retención, ingresos y uso de clientes.
2. Consulta políticas internas corporativas (Acuerdos de Nivel de Servicio, Arquitectura Cloud, Privacidad) almacenadas en PDFs.
3. Bloquea de inmediato cualquier pregunta que esté fuera del dominio B2B (ej. chistes, recetas, temas generales), garantizando un tono estrictamente profesional.

---

## 2. Visión Arquitectónica (¿Cómo lo hace?)

AuraComm rompe con el paradigma de los LLMs tradicionales (que tienden a alucinar o inventar datos) implementando una **Arquitectura Determinista, Declarativa y Cloud-Native**:

- **Cloud-Native & Stateless:** El agente no almacena bases de datos de clientes ni PDFs en su disco duro local. Se conecta directamente a un *Data Lake* (MinIO/S3) usando credenciales seguras (Boto3). Todo el procesamiento de los documentos corporativos y los conjuntos de datos masivos (CSVs) ocurre *in-memory* al arrancar el servidor.
- **Orquestación ReAct (Reasoning and Acting):** Utiliza LangGraph para modelar un grafo de estados conversacional, permitiéndole al motor cognitivo (Groq / Llama 3.1) "pensar" qué herramienta necesita usar antes de responder.
- **Capa Semántica Declarativa (Metadata-Driven):** En lugar de que el modelo escriba código o consulte bases de datos libremente (lo que genera vulnerabilidades RCE), NovaSync posee un catálogo estricto de reglas de negocio (`metrics_catalog.json`). El Agente simplemente "escoge" una métrica y el motor interno de Python resuelve el filtro matemático usando Pandas nativo.

---

## 3. Entradas y Salidas (¿Qué toma y qué retorna?)

**Entradas (Inputs):**
- **Datos Estáticos (Cloud):** 
  - Archivos tabulares: `Client.csv` y `Record.csv`.
  - Documentos corporativos: PDFs (Ej. `DOC-FIN-004`, `DOC-ARCH-001`).
- **Input del Usuario:** Consultas en lenguaje natural ingresadas a través del chat (Streamlit).

**Salidas (Outputs):**
- **Respuestas Cualitativas:** Extractos precisos o resúmenes de documentos internos de políticas.
- **Respuestas Cuantitativas:** Valores numéricos exactos calculados matemáticamente.
- **Manejo de Errores/Rechazos:** Mensajes predefinidos y elegantes si el usuario pregunta algo fuera del dominio, o si el documento/métrica no existe en los registros.
- **Telemetría de UI:** Notificaciones asíncronas en pantalla mostrando qué herramienta está usando ("Analizando PDFs...", "Calculando KPIs...").

---

## 4. Flujo de Ejecución (End-to-End)

El ciclo de vida de una consulta en NovaSync se divide en las siguientes etapas secuenciales:

### Etapa 1: Ingesta y Vectorización (Arranque del Servidor)
1. Al arrancar `main.py`, el sistema lee el *Data Lake* (MinIO).
2. Los CSVs se cargan directamente en DataFrames de Pandas (`s3fs`).
3. Los PDFs corporativos se extraen, se limpian y se fragmentan semánticamente mediante un `RecursiveCharacterTextSplitter`.
4. Los fragmentos de texto se convierten a vectores (Embeddings locales de HuggingFace `all-MiniLM-L6-v2`) y se almacenan en una base de datos vectorial en memoria (**FAISS**).

### Etapa 2: Recepción y Enrutamiento de la Pregunta
1. El usuario envía su pregunta desde Streamlit.
2. El orquestador (`orcuestrator.py`) inyecta un *System Prompt* severo (anti-alucinaciones) junto con el historial de chat persistente (SQLite).
3. El LLM (Cerebro Cognitivo) analiza la intención del usuario y decide si necesita invocar una herramienta:
   - Si es texto/políticas $\rightarrow$ `consultar_politicas_pdf`.
   - Si es un número/KPI $\rightarrow$ `consultar_kpi_empresarial`.
   - Si es irrelevante (ej. "Cuéntame un chiste") $\rightarrow$ Rechaza internamente sin llamar herramientas.

### Etapa 3: Ejecución de Herramientas (Procesamiento Interno)

**Ruta A: Capa Semántica (KPIs)**
1. El Agente usa Pydantic para validar dinámicamente si la métrica solicitada está listada en `metrics_catalog.json`. Si no está, Pydantic lanza una alerta, el LLM la lee y le dice al usuario "No tengo esa métrica".
2. Si es válida, el `semantic_layer.py` lee los filtros (ej. `churn == 0`) del JSON y los aplica nativamente y de forma determinista usando el DataFrame. Retorna el número exacto.

**Ruta B: Búsqueda Vectorial (RAG)**
1. La herramienta de RAG busca en el índice vectorial FAISS los fragmentos más relevantes.
2. Un sub-prompt interno analiza el texto recuperado aplicando la **Regla #5 (Filtro Anti-Alucinación)**: Si el usuario solicitó el documento `DOC-FIN-004`, el LLM verifica literalmente que ese código esté impreso en el texto. Si no, falla intencionalmente diciendo que no tiene la información.
3. Si el documento es correcto, extrae el resumen.

### Etapa 4: Síntesis y Renderizado
1. El Orquestador recibe el dato exacto (el número del KPI o el texto del PDF).
2. Formula una respuesta conversacional profesional ("El número de clientes activos es de X").
3. Streamlit consume la respuesta usando `st.write_stream`, dándole al usuario final un efecto de máquina de escribir inmersivo.
