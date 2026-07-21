import pandas as pd
import json
import os
import logging

logger = logging.getLogger(__name__)

OPERACIONES_VALIDAS = {"conteo", "promedio", "maximo", "valor_exacto", "suma", "argmax", "group_by_max", "correlacion_pearson", "percentil_75_promedio"}
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
            
            # Validaciones específicas de las nuevas operaciones
            if config["operacion"] in ["promedio", "suma", "maximo"] and "columna_objetivo" not in config:
                raise ValueError(f"Métrica '{nombre}' con operación '{config['operacion']}' requiere 'columna_objetivo'")
            if config["operacion"] == "argmax" and ("columna_objetivo" not in config or "id_columna" not in config):
                raise ValueError(f"Métrica '{nombre}' con 'argmax' requiere 'columna_objetivo' e 'id_columna'")
            if config["operacion"] == "group_by_max" and ("columna_objetivo" not in config or "group_col" not in config):
                raise ValueError(f"Métrica '{nombre}' con 'group_by_max' requiere 'columna_objetivo' y 'group_col'")
            if config["operacion"] == "correlacion_pearson" and "cols" not in config:
                raise ValueError(f"Métrica '{nombre}' con 'correlacion_pearson' requiere lista 'cols' de 2 elementos")
            if config["operacion"] == "percentil_75_promedio" and ("columna_percentil" not in config or "columna_objetivo" not in config):
                raise ValueError(f"Métrica '{nombre}' con 'percentil_75_promedio' requiere 'columna_percentil' y 'columna_objetivo'")
                
            for filtro in config.get("filtros", []):
                if filtro.get("operador") not in OPERADORES_VALIDOS:
                    raise ValueError(f"Métrica '{nombre}' tiene operador inválido '{filtro.get('operador')}'. Válidos: {OPERADORES_VALIDOS}")
        logger.info("Catálogo de métricas validado: %d KPIs correctos.", len(self.catalogo))

    def _aplicar_filtro(self, df, col, op, val):
        if col not in df.columns:
            raise KeyError(f"Columna '{col}' no existe en el DataFrame.")
        
        # Casteo automático al tipo de la columna
        tipo_col = df[col].dtype
        try:
            if pd.api.types.is_numeric_dtype(tipo_col):
                val = float(val) if '.' in str(val) else int(val)
        except Exception:
            pass

        if op == "==":
            return df[df[col] == val]
        elif op == ">":
            return df[df[col] > val]
        elif op == "<":
            return df[df[col] < val]
        elif op == "!=":
            return df[df[col] != val]
        elif op == ">=":
            return df[df[col] >= val]
        elif op == "<=":
            return df[df[col] <= val]
        return df

    def ejecutar_kpi(self, metric_name: str, filtros_dinamicos: list = None) -> str:
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
                df = self._aplicar_filtro(df, filtro["columna"], filtro["operador"], filtro["valor"])

            # 2. Aplicar múltiples filtros dinámicos
            if filtros_dinamicos:
                for filtro in filtros_dinamicos:
                    df = self._aplicar_filtro(df, filtro["columna"], filtro["operador"], filtro["valor"])
        except KeyError as e:
            logger.error(f"Error de filtro KeyError: {e}")
            return f"Error interno: {e}"

        if df.empty:
            return "Error: No se encontraron registros que coincidan con los filtros solicitados."

        # 3. Ejecutar la operación matemática avanzada
        op = config["operacion"]
        try:
            if op == "conteo":
                resultado = int(df.shape[0])
            elif op == "promedio":
                resultado = float(round(df[config["columna_objetivo"]].mean(), 2))
            elif op == "maximo":
                resultado = float(round(df[config["columna_objetivo"]].max(), 2))
            elif op == "suma":
                resultado = float(round(df[config["columna_objetivo"]].sum(), 2))
            elif op == "valor_exacto":
                if len(df) > 1:
                    logger.warning(f"Anomalía: Se esperaban 1 registro exacto pero se encontraron {len(df)}")
                resultado = df[config["columna_objetivo"]].iloc[0]
                if hasattr(resultado, 'item'):
                    resultado = resultado.item()
            elif op == "argmax":
                idx_max = df[config["columna_objetivo"]].idxmax()
                val_id = df.loc[idx_max, config["id_columna"]]
                val_max = df.loc[idx_max, config["columna_objetivo"]]
                resultado = f"{config['id_columna']}: {val_id} (Valor: {val_max})"
            elif op == "group_by_max":
                grouped = df.groupby(config["group_col"])[config["columna_objetivo"]].mean()
                cat_max = grouped.idxmax()
                val_max = grouped.max()
                resultado = f"Categoría: {cat_max} (Promedio: {val_max:.2f})"
            elif op == "correlacion_pearson":
                col1, col2 = config["cols"]
                corr = df[col1].corr(df[col2])
                resultado = float(round(corr, 4))
            elif op == "percentil_75_promedio":
                p75 = df[config["columna_percentil"]].quantile(0.75)
                df_top = df[df[config["columna_percentil"]] >= p75]
                promedio = df_top[config["columna_objetivo"]].mean()
                resultado = float(round(promedio, 2))
            else:
                return f"Error: Operación '{op}' no soportada."
        except Exception as e:
            return f"Error en el cálculo: {e}"

        return f"Éxito. Resultado de la métrica {metric_name_str}: {resultado}"
