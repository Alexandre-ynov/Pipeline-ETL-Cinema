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
    raise RuntimeError("Configurez JETON ou CLE_API dans le fichier .env.")

try:
    collections=[]
    for collection_id in range(1, 3): 
        url = f"https://api.themoviedb.org/3/discover/movie?" 
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
    print("Données extraites de l'API avec succès :")
    print(f"Réponse enregistrée dans : {output_file}")
except requests.exceptions.RequestException as error:
    print(f"Erreur de connexion ou de requête à l'API : {error}")
except json.JSONDecodeError:
    print("Erreur : la réponse de l'API n'est pas un JSON valide.")

