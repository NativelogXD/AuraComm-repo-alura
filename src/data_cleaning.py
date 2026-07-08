import pandas as pd
import os

def fase4_limpiar_csvs():
    """Carga y limpia los DataFrames eliminando nulos y duplicados."""
    df_c, df_r = None, None
    
    if os.path.exists("data\Client.csv"):
        df_c = pd.read_csv("data\Client.csv")
        df_c.dropna(how="all", inplace=True)
        df_c.drop_duplicates(inplace=True)
        print(f"Client.csv procesado y limpio. {len(df_c)} registros listos.")
        
    if os.path.exists("data\Record.csv"):
        df_r = pd.read_csv("data\Record.csv")
        df_r.dropna(how="all", inplace=True)
        df_r.drop_duplicates(inplace=True)
        if 'Latencia' in df_r.columns:
            df_r['Latencia'].fillna(0, inplace=True)
    return df_c, df_r

if __name__ == "__main__":
    print("Ejecutando limpieza de datos...")
    fase4_limpiar_csvs()
