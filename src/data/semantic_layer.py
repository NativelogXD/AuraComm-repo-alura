import pandas as pd
import json
import os
import logging

logger = logging.getLogger(__name__)

OPERACIONES_VALIDAS = {"conteo", "promedio", "maximo", "valor_exacto"}
OPERADORES_VALIDOS = {"==", ">", "<", "!=", ">=", "<="}

class SemanticLayer:
    """
    Capa Semántica (Semantic Layer) para NovaSync.
    Motor de ejecución declarativo puramente basado en metadatos (seguro contra RCE).
    """
    def __init__(self, df_client: pd.DataFrame, df_record: pd.DataFrame):
        self.datasets = {
            "client": df_client,
            "record": df_record,
            "merged": pd.merge(df_client, df_record, on="Customer_ID", how="inner")
        }
        
        # Cargar el catálogo de métricas
        catalog_path = os.path.join(os.path.dirname(__file__), "metrics_catalog.json")
        with open(catalog_path, "r", encoding="utf-8") as f:
            self.catalogo = json.load(f)
        
        # Tip #3: Validar schema del catálogo al arrancar
        self._validar_catalogo()

    def _validar_catalogo(self):
        """Valida que cada entrada del catálogo JSON tenga los campos obligatorios."""
        for nombre, config in self.catalogo.items():
            if "df" not in config:
                raise ValueError(f"Métrica '{nombre}' sin campo 'df' en metrics_catalog.json")
            if config["df"] not in self.datasets:
                raise ValueError(f"Métrica '{nombre}' referencia DataFrame '{config['df']}' que no existe. Válidos: {list(self.datasets.keys())}")
            if "operacion" not in config:
                raise ValueError(f"Métrica '{nombre}' sin campo 'operacion' en metrics_catalog.json")
            if config["operacion"] not in OPERACIONES_VALIDAS:
                raise ValueError(f"Métrica '{nombre}' tiene operación inválida '{config['operacion']}'. Válidas: {OPERACIONES_VALIDAS}")
            if config["operacion"] == "promedio" and "columna_objetivo" not in config:
                raise ValueError(f"Métrica '{nombre}' con operación 'promedio' requiere campo 'columna_objetivo'")
            for filtro in config.get("filtros", []):
                if filtro.get("operador") not in OPERADORES_VALIDOS:
                    raise ValueError(f"Métrica '{nombre}' tiene operador inválido '{filtro.get('operador')}'. Válidos: {OPERADORES_VALIDOS}")
        logger.info("Catálogo de métricas validado: %d KPIs correctos.", len(self.catalogo))

    def ejecutar_kpi(self, metric_name: str, filtro_dinamico: dict = None) -> str:
        """
        Ejecuta de forma segura un KPI leyendo las reglas del JSON.
        """
        metric_name_str = str(metric_name).lower()
        
        if metric_name_str not in self.catalogo:
            return f"Error: La métrica '{metric_name_str}' no existe en el catálogo."
            
        config = self.catalogo[metric_name_str]
        df = self.datasets.get(config["df"])
        
        if df is None:
            return f"Error: DataFrame '{config['df']}' no encontrado."

        try:
            # 1. Aplicar filtros estáticos
            for filtro in config.get("filtros", []):
                col, op, val = filtro["columna"], filtro["operador"], filtro["valor"]
                if op == "==":
                    df = df[df[col] == val]
                elif op == ">":
                    df = df[df[col] > val]
                elif op == "<":
                    df = df[df[col] < val]
                elif op == "!=":
                    df = df[df[col] != val]
                elif op == ">=":
                    df = df[df[col] >= val]
                elif op == "<=":
                    df = df[df[col] <= val]

            # 2. Aplicar filtros dinámicos (inyectados por el LLM tras pasar la validación Pydantic)
            if filtro_dinamico:
                for col, val in filtro_dinamico.items():
                    # Casteo automático al tipo de la columna
                    tipo_col = df[col].dtype
                    try:
                        if pd.api.types.is_numeric_dtype(tipo_col):
                            val = float(val) if '.' in str(val) else int(val)
                    except:
                        pass
                    df = df[df[col] == val]
        except KeyError as e:
            logger.error(f"Error de filtro KeyError: {e}")
            return "Error interno: La dimensión de filtrado solicitada no existe en la base de datos."

        # 3. Ejecutar la operación matemática
        if config["operacion"] == "conteo":
            resultado = int(df.shape[0])
        elif config["operacion"] == "promedio":
            resultado = float(round(df[config["columna_objetivo"]].mean(), 2))
        elif config["operacion"] == "maximo":
            resultado = float(round(df[config["columna_objetivo"]].max(), 2))
        elif config["operacion"] == "valor_exacto":
            if df.empty:
                return "Error: No se encontraron registros que coincidan con el filtro solicitado."
            if len(df) > 1:
                logger.warning(f"Anomalía: Se esperaban 1 registro exacto pero se encontraron {len(df)}")
            resultado = df[config["columna_objetivo"]].iloc[0]
            # Convertir numpy types a python nativo si aplica
            if hasattr(resultado, 'item'):
                resultado = resultado.item()
        else:
            return f"Error: Operación '{config['operacion']}' no soportada."

        return f"Éxito. Resultado de la métrica {metric_name_str}: {resultado}"
