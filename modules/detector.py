import json
import pandas as pd
import numpy as np

pd.options.future.infer_string = True


def outlier_detection(df):
    numeric_df = df.select_dtypes(include=np.number)
    outlier_report = {}
    for col in numeric_df.columns:
        Q1 = numeric_df[col].quantile(0.25)
        Q3 = numeric_df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        outliers = numeric_df[(numeric_df[col] < lower_bound) | (numeric_df[col] > upper_bound)]
        outlier_report[col] = int(len(outliers))
    return outlier_report


def spe_char_issue(df):
    # Buscamos caracteres que no sean alfanuméricos en columnas de texto
    spe_char_report = []
    text_cols = df.select_dtypes(include=['object', 'string']).columns
    pattern = r'[^a-zA-Z0-9\s]'

    for col in text_cols:
        # Verificamos si algún registro contiene el patrón
        if df[col].astype(str).str.contains(pattern, regex=True).any():
            spe_char_report.append(col)
    return spe_char_report


def format_issues(df):
    textual_df = df.select_dtypes(include=['object', 'string'])
    columns_with_upper = []
    columns_lower = []

    for col in textual_df.columns:
        # Verificamos si todos los registros están en mayúsculas (ignorando nulos)
        if textual_df[col].astype(str).str.isupper().all():
            columns_with_upper.append(col)
        # Verificamos si todos están en minúsculas
        elif textual_df[col].astype(str).str.islower().all():
            columns_lower.append(col)

    return columns_with_upper, columns_lower


def detect(csv_path: str):
    try:
        csv_analyze = pd.read_csv(csv_path)
    except Exception as e:
        return json.dumps({"error": f"No se pudo leer el archivo: {str(e)}"})

    # Detección de Nulos y Duplicados (Forma eficiente)
    columns_with_na = csv_analyze.columns[csv_analyze.isna().any()].tolist()

    # Columnas que tienen valores duplicados
    columns_with_duplicates = [col for col in csv_analyze.columns if csv_analyze[col].duplicated().any()]

    outlier_report = outlier_detection(csv_analyze)
    spe_char_report = spe_char_issue(csv_analyze)
    columns_with_upper, columns_lower = format_issues(csv_analyze)

    final_detection_report = {
        'columns_with_na': columns_with_na,
        'columns_with_duplicates': columns_with_duplicates,
        'outlier_report': outlier_report,
        'special_char_report': spe_char_report,
        'columns_with_upper': columns_with_upper,
        'columns_lower': columns_lower,
        'dataframe_general_info' : csv_analyze.describe().to_string(),
        'dataframe_shape' : str(csv_analyze.shape),
    }

    return json.dumps(final_detection_report, indent=4, default=str) , csv_analyze

#Aqui deberia lanzar el json y el dataframe para entonces el cliente pasar json y un dataframe al cleaner y entonces el cleaner mapea el dataframe y activa las funciones del toolset