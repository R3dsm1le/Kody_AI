import json
import time
from modules.LeMistral_client import lemistral_rescue_me
from modules.toolset import *
from tqdm import tqdm



strategies_dict = {
    # Missing value handling
    "fill_with_median": fill_with_median,
    "fill_with_mean": fill_with_mean,
    "fill_with_zero": fill_with_zero,
    "fill_with_mode": fill_with_mode,
    "remove_null_rows": remove_null_rows,

    # Duplicate handling
    "remove_duplicates": remove_duplicates,
    "flag_duplicates": flag_duplicates,

    # Text transformations
    "convert_to_lowercase": convert_to_lowercase,
    "convert_to_uppercase": convert_to_uppercase,
    "title_case": title_case,
    "remove_spaces": remove_spaces,
    "normalize_characters": normalize_characters,

    # Type conversions
    "convert_to_numeric_float": convert_to_numeric_float,
    "convert_to_numeric_int": convert_to_numeric_int,
    "convert_to_date": convert_to_date,
    "convert_to_string": convert_to_string,

    # Outlier handling
    "remove_outliers": remove_outliers,
    "winsorize": winsorize,
    "get_outliers": get_outliers
}




def lemistral_helper_action(strategies_json, df):
    """
    Applies cleaning strategies to the DataFrame

    Args:
        strategies_json: List of strategies from Mistral's JSON
        df: Pandas DataFrame

    Returns:
        Clean DataFrame
    """

    # Preparar todas las operaciones
    operations = []
    for strategy in strategies_json:
        strategy_name = strategy.get('strategy', '')
        column_str = strategy.get('column', '')

        if ',' in column_str:
            columns = [col.strip() for col in column_str.split(',')]
        else:
            columns = [column_str.strip()]

        for column in columns:
            operations.append((strategy_name, column))

    # Barra de progreso con tqdm
    for strategy_name, column in tqdm(operations, desc="🧹 Cleaning data", unit="column"):

        # Verify that the strategy exists
        if strategy_name not in strategies_dict:
            tqdm.write(f"⚠️ Strategy '{strategy_name}' not found. Skipping...")
            continue

        # Verify that the column exists in the DataFrame
        if column not in df.columns:
            tqdm.write(f"⚠️ Column '{column}' not found. Skipping...")
            time.sleep(5)
            continue

        try:
            cleaning_function = strategies_dict[strategy_name]
            df = cleaning_function(df, column)
            tqdm.write(f"✓ Applied {strategy_name} to: {column}")
            time.sleep(5)
        except Exception as e:
            tqdm.write(f"❌ Error applying {strategy_name} to {column}: {e}")

    return df


