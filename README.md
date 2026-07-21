# NovaSync Solutions: Agente Inteligente B2B (AuraComm)

AuraComm es el nucleo cognitivo de NovaSync Solutions, una corporacion simulada del sector de Telecomunicaciones e Infraestructura de Red B2B. Este repositorio contiene el codigo fuente de un agente de Inteligencia Artificial corporativo, disenado con una arquitectura Cloud-Native, Determinista y de Alta Seguridad.

El objetivo del agente AuraComm es asistir a gerentes, ejecutivos de finanzas y analistas de red, resolviendo consultas complejas sobre la infraestructura de telefonia, facturacion, niveles de servicio (SLA) y auditorias de hardware, utilizando bases de datos corporativas centralizadas en un Data Lake.

---

## Arquitectura de la Solucion (Hibrida y Segura)

A diferencia de los chatbots convencionales, AuraComm emplea un diseno determinista que mitiga las alucinaciones de datos mediante un orquestador que sigue estrictas reglas de negocio.

La arquitectura se divide en capas de inteligencia y procesamiento:

1. Cerebro Orquestador (Gemini 3.1 Flash Lite): El agente principal, impulsado por LangGraph. Analiza la intencion del usuario, aplica Query Expansion para mapear lenguaje natural a jerga tecnica corporativa, consulta herramientas, verifica precondiciones (Guardrails) y ensambla la respuesta final con un tono B2B profesional.
2. Sub-Agente RAG (Groq - Llama 3.1 8B): Especializado exclusivamente en leer documentos tecnicos recuperados del indice vectorial a velocidades ultrarrapidas y devolver extracciones limpias en formato JSON estructurado.
3. Motor Local de Embeddings (all-MiniLM-L6-v2): La vectorizacion de documentos se realiza en local, garantizando total independencia de cuotas de APIs externas y brindando maxima privacidad.
4. Integracion de Datos (Cloud Data Lake - S3): Toda la fuente de verdad (archivos CSV de bases de datos y PDFs corporativos) vive en la nube (S3). La aplicacion actua como un motor de procesamiento Stateless que consulta, descarga en memoria y procesa con Pandas o FAISS de forma dinamica sin saturar el disco. Se incluye un sistema de ETags (MD5) para asegurar que la reconstruccion del indice FAISS solo ocurra si existen cambios reales en el origen de datos.

---

## Tecnologias Utilizadas

- Frontend: Streamlit (Interfaz asincrona).
- Core IA: LangChain & LangGraph (Memoria persistente via SQLite).
- Modelos: Gemini API, Groq API, HuggingFace Local Embeddings.
- Busqueda Vectorial: FAISS con recuperacion MMR (Maximal Marginal Relevance).
- Data Lake Cloud: S3 Compatible (Boto3 / S3fs).
- Procesamiento de Datos: Pandas.
- Despliegue: Docker, Docker Compose.

---

## Configuracion y Ejecucion Local

Sigue estos pasos para arrancar el agente en tu entorno de desarrollo local.

### 1. Clonar e Instalar
```bash
# Navega a la carpeta principal
cd AuraComm/src

# Crea y activa tu entorno virtual
python -m venv .venv
.\.venv\Scripts\activate   # En Windows
# source .venv/bin/activate # En Linux/Mac

# Instala las dependencias
pip install -r requirements.txt
```

### 2. Configurar el Entorno (.env)
En el directorio `src/`, crea un archivo `.env`. Este agente utiliza una configuracion multi-modelo para optimizar costos y latencia:

```env
# Cerebro B2B Principal (Orquestador)
GEMINI_API_KEY=tu_clave_gemini_aqui

# Sub-Agente RAG (Extraccion Rapida de Texto)
GROQ_API_KEY=gsk_tu_clave_groq_aqui
```

### 3. Iniciar el Agente
```bash
python -m streamlit run main.py
```
Nota: La primera ejecucion tomara tiempo adicional mientras se descarga el modelo de HuggingFace y se construye por primera vez el indice vectorial FAISS desde el almacenamiento S3.

---

## Despliegue en Produccion (Docker)

El proyecto incluye un `Dockerfile` optimizado y un `docker-compose.yml`. Esta listo para ser desplegado en plataformas como Dokploy, Coolify o servidores on-premise.

1. Construye e inicia el contenedor:
   ```bash
   docker-compose up -d --build
   ```
2. Volumenes Persistentes: La configuracion de Docker incluye un volumen para `/app/db`. Esto garantiza que las bases de datos de sesion de SQLite y los indices en cache de FAISS sobrevivan a los reinicios del contenedor.

---

## Ejemplos de Interaccion (Casos de Uso)

El agente AuraComm comprende la capa semantica de NovaSync Solutions. Es posible realizar consultas como:
- "¿Bajo que circunstancias especificas un cliente tiene derecho a recibir creditos de servicio proporcionales segun el SLA de NovaSync?" (Analisis de Documentos RAG).
- "¿Que par de variables se utilizan para contabilizar y gestionar la cantidad de sub-dispositivos fisicos o equipos registrados asociados a un mismo tenant?" (Uso de Query Expansion).
- "¿Que kpis manejas?" (Listado dinamico desde el catalogo semantico de metricas).
- "¿Cuantos clientes cancelaron su suscripcion este mes y cual era su ingreso promedio?" (Analisis tabular).
