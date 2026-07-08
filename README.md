# NovaSync: Agente Digital B2B (Arquitectura Determinista)

## 📌 Descripción General del Proyecto

**NovaSync B2B** es un agente de inteligencia artificial corporativo diseñado para interactuar con gerentes y clientes empresariales. El agente tiene acceso seguro a bases de datos corporativas (documentos PDF de arquitectura/soporte y bases de datos tabulares de clientes) para resolver consultas complejas en tiempo real. 

A diferencia de los chatbots tradicionales, este proyecto emplea una **Arquitectura Determinista**. Esto significa que las herramientas, bases de datos y formatos de salida están estrictamente controlados mediante validación estructurada, impidiendo que el LLM alucine datos corporativos.

---

## 🏗️ Arquitectura de la Solución

El núcleo del sistema está construido sobre un grafo de estados (**StateGraph**) que orquesta el razonamiento de la IA:

1. **Orquestador (LangGraph)**: Controla el flujo cognitivo del agente. Permite mantener el historial conversacional (Memoria) y tomar decisiones de enrutamiento (ej. saber cuándo usar una herramienta y cuándo responder al usuario).
2. **Sistema RAG Optimizado (Retrieval-Augmented Generation)**: 
   - Procesa PDFs corporativos y los almacena en un índice vectorial local (**FAISS**).
   - Utiliza `MultiQueryRetriever` con recuperación controlada (`k=2`) para evitar sobrecargar la ventana de contexto de los LLM.
   - Cuenta con un sistema de **MD5 Checksum** que detecta automáticamente si los PDFs fueron modificados para reconstruir los embeddings solo cuando es estrictamente necesario.
3. **Análisis Estructurado de Datos (CSV)**: En lugar de usar agentes de código vulnerable, utiliza herramientas nativas de Python (Pandas) encapsuladas bajo esquemas estrictos de **Pydantic** para leer y filtrar datos estructurados (ej. registros de clientes).
4. **Human-in-the-Loop (HITL)**: Implementa una capa de seguridad donde cualquier ejecución de herramientas internas (lectura de PDFs, acceso a bases de datos) queda pausada a la espera de **aprobación manual del administrador**.
5. **Interceptador Anti-Alucinaciones XML**: Un parche de ingeniería (Regex Parser) a nivel de orquestador que intercepta las fugas de formato del LLM (ej. cuando la IA intenta escupir llamadas a herramientas en texto plano) y las convierte internamente en la API estructurada nativa de LangChain.

---

## 🛠️ Tecnologías y Herramientas Utilizadas

- **Lenguaje**: Python 3.10+
- **Orquestación IA**: LangChain & LangGraph
- **Modelos de Lenguaje (LLM)**: Groq (Llama 3.1 8B Instant) / Gemini 2.5 Flash
- **Modelos de Embeddings**: HuggingFace (`intfloat/multilingual-e5-small`)
- **Base de Datos Vectorial**: FAISS (Facebook AI Similarity Search)
- **Procesamiento de Datos Tabulares**: Pandas
- **Validación Estructurada**: Pydantic
- **Base de Datos de Memoria**: SQLite (`checkpoints_auracomm.db`)

---

## 🚀 Instrucciones de Ejecución

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
   Asegúrate de tener un archivo `.env` en la carpeta `src/` con tus claves de API:
   ```env
   GROQ_API_KEY=gsk_tu_clave_aqui
   GEMINI_API_KEY=AIzaSy_tu_clave_aqui
   ```

4. **Ejecutar el Agente:**
   ```bash
   python main.py
   ```
   *La primera ejecución tomará unos segundos extra mientras descarga el tokenizador de HuggingFace y construye el índice FAISS inicial.*

---

## 💬 Ejemplos de Interacción

### ❓ Ejemplo de Preguntas
- *"Háblame acerca del documento DOC-ARCH-001 y de qué trata."*
- *"¿Cuáles son las políticas de privacidad según el documento DOC-PRIV-003?"*
- *"Dame información sobre los clientes que han cancelado nuestros servicios este año."*
- *"Cuéntame un chiste."* *(Para probar el escudo anti-prompting)*

### 🤖 Ejemplo de Respuestas del Agente

**Consulta:** *"¿Cuáles son las políticas de privacidad según el documento DOC-PRIV-003?"*

**Salida en consola:**
```text
[⚠️ ALERTA HITL]: El agente solicita ejecutar una herramienta interna.
 -> Herramienta: consultar_politicas_pdf
 -> Argumentos: {'consulta': 'documento DOC-PRIV-003'}
¿Aprobar ejecución? (s = sí / n = no): s
[✔️ Aprobado. Procesando...]

[🤖 AuraComm]: El documento DOC-PRIV-003 trata sobre la protección de datos de los clientes de NovaSync. 
- NovaSync cumple con los estándares internacionales de la Unión Europea (GDPR) y de California (CCPA).
- Se aplican medidas de seguridad desde la recopilación hasta la eliminación de los datos de los clientes.
```

**Consulta (Fuera de dominio):** *"Escribe un poema sobre el mar."*

**Salida en consola:**
```text
[🤖 AuraComm]: Lo siento, soy un agente corporativo exclusivo de NovaSync. Solo estoy autorizado para asistir en temas relacionados con nuestros servicios, políticas técnicas y bases de clientes B2B. ¿En qué te puedo ayudar respecto a la corporación?
```

---

## ⚠️ Advertencias y Recomendaciones (API Limits)

Este proyecto está diseñado para funcionar en un entorno de capa gratuita (Free Tier), por lo que se deben tener en cuenta las siguientes protecciones implementadas:

1. **Límites de Tokens por Minuto (Groq TPM)**:
   - Los modelos gratuitos de Groq tienen un límite estricto de **6000 Tokens Por Minuto (TPM)**. 
   - **Solución implementada:** Para evitar que el historial conversacional crezca infinitamente y rompa este límite, el orquestador tiene un **Recortador de Memoria a Corto Plazo** que solo envía los últimos 5 mensajes al LLM. Además, el RAG fue capado a `k=2` fragmentos para aligerar el payload.
   
2. **Ráfagas de Peticiones (Rate Limits)**:
   - Si decides cambiar el motor en `models.py` para usar **Google Gemini 2.5 Flash**, ten en cuenta que la API gratuita solo permite **15 peticiones por minuto**. Dado que LangGraph hace peticiones múltiples por cada interacción (decidir herramienta -> ejecutar -> responder), hacer dos preguntas muy rápido causará un error `429 RESOURCE_EXHAUSTED`.
   - **Recomendación:** Espera ~15 segundos entre preguntas si usas la API de Gemini, o mantén el código actual con **Llama 3.1 8B en Groq**, el cual ofrece una cuota generosa ideal para evaluaciones y testing ininterrumpido.

3. **Memoria (Checkpoints)**:
   - Si la terminal falla inesperadamente por cuotas excedidas, se recomienda limpiar el caché de memoria eliminando el archivo `checkpoints_auracomm.db` y reiniciar el script.
