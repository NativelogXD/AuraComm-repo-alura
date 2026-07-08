from pydantic import BaseModel, Field

# ==========================================
# PLANTILLAS DE ENTRADA (INPUT SCHEMAS)
# ==========================================

class ConsultaCSVInput(BaseModel):
    """Esquema para validar la entrada a la herramienta de análisis de datos."""
    consulta: str = Field(
        description="La pregunta detallada sobre datos tabulares o matemáticos (MRR, Clientes, Latencia, Uso, Cancelaciones)."
    )

class ConsultaPDFInput(BaseModel):
    """Esquema para validar la entrada a la herramienta de búsqueda de documentos."""
    consulta: str = Field(
        description="La pregunta sobre políticas corporativas, documentación técnica, arquitectura, SLA, privacidad o FAQ."
    )


# ==========================================
# PLANTILLAS DE SALIDA (OUTPUT SCHEMAS)
# ==========================================

class CodigoPandas(BaseModel):
    """Esquema para obligar al LLM a devolver código ejecutable sin charlatanería."""
    codigo: str = Field(
        description="Código Python puro para ejecutar en pandas. No debe contener etiquetas markdown ni texto adicional, solo código ejecutable."
    )

class ResultadoRAG(BaseModel):
    """Esquema de seguridad estricto para respuestas basadas en documentos (Anti-Hallucinations Guardrail)."""
    cita_textual: str = Field(
        description="Fragmento exacto extraído del documento fuente. Si no existe, pon 'Ninguna'."
    )
    es_informacion_inventada: bool = Field(
        description="True si parte de la respuesta no está en el contexto y tuviste que deducirla o alucinarla. False si es 100% fiel al contexto."
    )
    respuesta: str = Field(
        description="Respuesta detallada basada ÚNICAMENTE en el contexto. Si 'es_informacion_inventada' es True, debes negarte a responder y decir que careces de información."
    )
    certeza: str = Field(
        description="Nivel de confianza de la extracción: Alta, Media o Baja, dependiendo de la claridad del contexto."
    )
