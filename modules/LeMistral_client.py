import requests
import json
import os
from modules.detector import detect
from dotenv import load_dotenv

load_dotenv()

available_strategies = {
    "numerical_null_values": [
        "fill_with_median",
        "fill_with_mean",
        "fill_with_zero",
        "remove_null_rows"
    ],
    "categorical_null_values": [
        "fill_with_mode",
        "remove_null_rows"
    ],
    "duplicates": [
        "remove_duplicates",
        "flag_duplicates"
    ],
    "text_inconsistencies": [
        "convert_to_lowercase",
        "convert_to_uppercase",
        "title_case",
        "remove_spaces",
        "normalize_characters"
    ],
    "incorrect_types": [
        "convert_to_numeric",
        "convert_to_date",
        "convert_to_string"
    ],
    "outliers": [
        "remove_outliers_iqr",
        "winsorize",
        "keep_outliers"
    ]
}

csv = ''

def get_csv():
    return csv

def set_csv(csv_set):
    global csv
    csv = csv_set

def lemistral_rescue_me(mode="concise"):
    try:
        detect_report,df= detect(get_csv())
        max_report_length = 3000  # Reducido
        if len(detect_report) > max_report_length:
            detect_report = detect_report[:max_report_length] + "..."

        url = "https://api.mistral.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {os.getenv('MISTRAL_API_KEY')}",
            "Content-Type": "application/json"
        }

        # Diferentes estilos de prompt
        prompts = {
            "concise": "Be brief. List only top 3 critical issues.",
            "detailed": "Provide comprehensive analysis with examples.",
            "simple": "Use simple strategies. Avoid complex parameters."
        }

        payload = {
            "model": "mistral-large-latest",  # Cambiado a small
            "temperature": 0.5,  # Menos aleatorio
            "max_tokens": 1500,  # Limitado
            "messages": [
                {
                    "role": "user",
                    "content": f"""
                    Data cleaning expert task. {prompts.get(mode, prompts['concise'])}

                    Problems: {detect_report}
                    Available: {available_strategies}
                    focus on the top 5 issues 
                    JSON format only:
                    {{"strategies": [{{"column": "", "problem": "", "strategy": "", "parameters": {{}}, "reason": ""}}]}}
                    """
                }
            ]
        }

        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result =  response.json()
        # EXTRAER SOLO LAS ESTRATEGIAS LIMPIAS
        content = result['choices'][0]['message']['content']

        # Remover markdown code blocks (```json y ```)
        content = content.replace('```json', '').replace('```', '').strip()

        # Remover saltos de línea y espacios extra
        content = content.replace('\n', '').replace('  ', ' ')

        # Parsear JSON
        strategies_data = json.loads(content)

        # Retornar solo las estrategias
        return strategies_data['strategies'] , df

    except Exception as e:
        print(f"Error: {e}")
        return None