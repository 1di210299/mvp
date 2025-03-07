# connectors/openai_connector.py
import requests
import os

# Asegúrate de definir la variable de entorno OPENAI_API_KEY con tu clave.
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_API_URL = "https://api.openai.com/v1/engines/davinci-codex/completions"  # Ajusta el endpoint y modelo si es necesario

def analyze_data(prompt: str) -> dict:
    """
    Envía un prompt a la API de OpenAI y devuelve la respuesta.
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    data = {
        "prompt": prompt,
        "max_tokens": 150,
        "n": 1,
        "stop": None,
        "temperature": 0.7
    }
    response = requests.post(OPENAI_API_URL, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.text}
