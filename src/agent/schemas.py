from pydantic import BaseModel, Field, field_validator
import json
import os

# ==========================================
# PLANTILLAS DE ENTRADA (INPUT SCHEMAS)
# ==========================================

def get_metricas_validas():
    catalog_path = os.path.join(os.path.dirname(__file__), "..", "data", "metrics_catalog.json")
    with open(catalog_path, "r", encoding="utf-8") as f:
        return list(json.load(f).keys())

class ConsultaKPIInput(BaseModel):
    """
    Esquema para invocar la Capa Semántica de KPIs.
    """
    metric_name: str = Field(
        ...,
        description=f"Nombre exacto de la métrica. Opciones válidas: {', '.join(get_metricas_validas())}"
    )
    filtro_dinamico: dict = Field(
        default=None,
        description="Filtro opcional adicional (ej. {'Customer_ID': 1000001}). ÚSALO SOLO cuando el usuario pregunte por un ID específico."
    )
    
    @field_validator('filtro_dinamico')
    def validar_filtro_dinamico(cls, v):
        if v is not None:
            # Lista blanca de columnas permitidas para evitar RCE o inyecciones
            columnas_permitidas = {"Customer_ID", "churn", "creditcd", "area"}
            for col in v.keys():
                if col not in columnas_permitidas:
                    raise ValueError(f"Columna de filtro '{col}' no permitida. Usar solo: {columnas_permitidas}")
        return v
    
    @field_validator('metric_name')
    def validar_metrica(cls, v):
        v = v.lower()
        metricas = get_metricas_validas()
        if v not in metricas:
            raise ValueError(f"Métrica inválida. Debe ser una de: {metricas}")
        return v

class ConsultaPDFInput(BaseModel):
    """Esquema para validar la entrada a la herramienta de búsqueda de documentos."""
    consulta: str = Field(
        description=(
            "Query semántica enriquecida y optimizada para buscar en los PDFs corporativos. "
            "REGLAS OBLIGATORIAS para construir esta query:\n"
            "1. NO pases la pregunta cruda del usuario. Extrae el TEMA CENTRAL.\n"
            "2. EXPANDE con sinónimos técnicos en inglés y español. "
            "Ejemplos: 'sub-dispositivos' → 'phones models devices equipos'; "
            "'tiempo de espera' → 'timeout unan sin respuesta'; "
            "'cargos por exceso' → 'overage datovr charges excedente'.\n"
            "3. Usa TÉRMINOS TÉCNICOS del dominio de telecomunicaciones B2B cuando sean aplicables.\n"
            "4. Combina el concepto de negocio + el término técnico en una sola query compacta. "
            "Ej: 'sub-dispositivos tenant phones models', 'timeout voz datos unan_vce unan_dat', "
            "'balanceo geográfico onboarding area'."
        )
    )

# ==========================================
# PLANTILLAS DE SALIDA (OUTPUT SCHEMAS)
# ==========================================

class ResultadoRAG(BaseModel):
    """Esquema de seguridad estricto para respuestas basadas en documentos (Anti-Hallucinations Guardrail)."""
    cita_textual: str = Field(
        description="Fragmento exacto extraído del documento fuente. Si no existe en el contexto, DEBES poner 'Ninguna'."
    )
    es_informacion_inventada: bool = Field(
        description="DEBES marcar True si la respuesta no se encuentra EXPLÍCITAMENTE en el contexto proporcionado, o si el contexto está vacío. Debes ser ultra-estricto: si el usuario pregunta por un código de documento específico (ej. DOC-FIN-004) y ese código NO aparece textualmente, DEBES marcar True sin importar si hay texto relacionado."
    )
    respuesta: str = Field(
        description="Respuesta detallada basada ÚNICAMENTE en el contexto. Si 'es_informacion_inventada' es True, responde 'No hay información en los documentos'."
    )
    certeza: str = Field(
        description="Nivel de confianza de la extracción: Alta, Media o Baja, dependiendo de la claridad del contexto."
    )
