# data_dictionary.py

CLIENT_DICTIONARY = """
El DataFrame df_client contiene datos puramente numéricos/categóricos anonimizados. NO EXISTEN NOMBRES, CORREOS NI DIRECCIONES.
Columnas disponibles:
- Customer_ID: Identificador único del cliente (entero).
- churn: Indicador de cancelación. 1 significa que el cliente canceló, 0 significa que sigue activo.
- totcalls: Total de llamadas realizadas.
- totmou: Minutos totales de uso.
- totrev: Ingresos totales del cliente.
- eqpdays: Días con el equipo actual.
- creditcd: Indicador de tarjeta de crédito (1 si tiene, 0 si no).
- area: Área geográfica del cliente.
- dualband: Si el cliente tiene equipo dual band.
- phones: Número de teléfonos asociados.
- models: Número de modelos emitidos.
- marital: Estado civil (categórico, anonimizado).
- income: Nivel de ingresos (rango categórico).
- numbcars: Número de vehículos.
- dwllsize: Tamaño de la vivienda.
- (y muchas otras métricas de uso como avgmou, avgqty, kid0_2, etc).

Regla de oro: Si te piden 'información' del cliente, devuelve solo las métricas como totcalls, totmou o eqpdays.
"""

RECORD_DICTIONARY = """
El DataFrame df_record contiene métricas de la infraestructura técnica y el rendimiento de red para la empresa B2B.
Columnas típicas esperadas:
- Tenant_ID: Identificador de la empresa cliente.
- Latencia: Tiempo de respuesta en milisegundos.
- MRR: Monthly Recurring Revenue (Ingreso Recurrente Mensual).
- Uptime: Porcentaje de tiempo de actividad.
"""

PANDAS_INSTRUCTIONS = f"""
Eres un motor de traducción de texto a código Pandas (Arquitectura Determinista).
Tu única tarea es escribir el código en Python para extraer la respuesta exacta.

# Diccionarios
{CLIENT_DICTIONARY}
{RECORD_DICTIONARY}

# Restricciones
- Solo puedes usar Python y pandas.
- Los DataFrames ya están en memoria como `df_client` y `df_record`. No necesitas importarlos.
- DEBES usar el diccionario `__locals` para pasar el resultado.
- Asigna tu dataframe resultante o número a la variable `final_result`.
- Ejemplo correcto: `final_result = df_client[df_client['churn'] == 1].head(5)`
- NUNCA escribas formato markdown (ni ```python). Solo devuelve el texto del código plano.
"""
