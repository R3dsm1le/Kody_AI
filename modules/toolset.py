import pandas as pd
from unidecode import unidecode

def fill_with_median(df, column):
    df[column] = df[column].fillna(df[column].median())
    return df

def fill_with_mean(df, column):
    df[column] = df[column].fillna(df[column].mean())
    return df

def fill_with_zero(df, column):
    df[column] = df[column].fillna(0)
    return df

def fill_with_mode(df, column):
    mode_val = df[column].mode()
    if not mode_val.empty:
        df[column] = df[column].fillna(mode_val[0])
    return df

def remove_null_rows(df, column):
    return df.dropna(subset=[column])

def remove_duplicates(df, column):
    return df.drop_duplicates(subset=[column], keep='first')

def flag_duplicates(df, column):
    df['es_duplicado'] = df.duplicated(subset=[column], keep=False)
    return df

def convert_to_lowercase(df, column):
    df[column] = df[column].astype(str).str.lower()
    return df

def convert_to_uppercase(df, column):
    df[column] = df[column].astype(str).str.upper()
    return df

def title_case(df, column):
    df[column] = df[column].astype(str).str.title()
    return df

def remove_spaces(df, column):
    df[column] = df[column].astype(str).str.strip()
    return df

def normalize_characters(df, column):
    df[column] = df[column].apply(lambda x: unidecode(str(x)) if pd.notnull(x) else x)
    return df

def convert_to_numeric_float(df, column):
    df[column] = pd.to_numeric(df[column], errors='coerce')
    return df

def convert_to_numeric_int(df, column):
    df[column] = pd.to_numeric(df[column], errors='coerce').round().astype('Int64')
    return df

def convert_to_date(df, column):
    df[column] = pd.to_datetime(df[column], errors='coerce')
    return df

def convert_to_string(df, column):
    df[column] = df[column].astype('string')
    return df

def remove_outliers(df, column):
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    return df[(df[column] >= lower_bound) & (df[column] <= upper_bound)].copy()

def winsorize(df, column):
    lower_limit = df[column].quantile(0.05)
    upper_limit = df[column].quantile(0.95)
    df[f'winsorized_{column}'] = df[column].clip(lower=lower_limit, upper=upper_limit)
    return df

def get_outliers(df, column):
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    return df[(df[column] < lower_bound) | (df[column] > upper_bound)].copy()

