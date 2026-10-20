import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("JETON")
api_key = os.getenv("CLE_API")

headers = {"accept": "application/json"}
params = {}
if token:
    headers["Authorization"] = f"Bearer {token}"
elif api_key:
    params["api_key"] = api_key
else:
    raise RuntimeError("Configure JETON or CLE_API in the .env file.")

try:
    url = "https://api.themoviedb.org/3/discover/movie?" 
    response = requests.get(url, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    data_api = response.json()
    output_dir = Path(__file__).resolve().parents[2] / "data" / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "movies_API.json"
    output_file.write_text(
        json.dumps(data_api, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print("Data successfully extracted from the API:")
    print(f"Response saved to: {output_file}")
except requests.exceptions.RequestException as error:
    print(f"API connection or request error: {error}")
except json.JSONDecodeError:
    print("Error: the API response is not valid JSON.")
