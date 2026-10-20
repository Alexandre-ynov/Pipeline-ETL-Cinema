import json
import os
import time
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

url = "https://api.themoviedb.org/3/discover/movie"
max_api_page = 500
delay_between_requests = 0.25

first_response = requests.get(
    url,
    headers=headers,
    params={**params, "page": 1},
    timeout=30,
)
first_response.raise_for_status()
api_data = first_response.json()

if not isinstance(api_data.get("results"), list):
    raise ValueError("La réponse de l'API ne contient pas de liste 'results'.")

api_total_pages = api_data.get("total_pages")
if not isinstance(api_total_pages, int) or api_total_pages < 1:
    raise ValueError("La réponse de l'API contient un total_pages invalide.")

pages_to_fetch = min(api_total_pages, max_api_page)
all_results = list(api_data["results"])

for page in range(2, pages_to_fetch + 1):
    time.sleep(delay_between_requests)
    response = requests.get(
        url,
        headers=headers,
        params={**params, "page": page},
        timeout=30,
    )
    response.raise_for_status()
    page_data = response.json()

    if page_data.get("page") != page or not isinstance(
        page_data.get("results"), list
    ):
        raise ValueError(f"Réponse invalide reçue pour la page {page}.")

    all_results.extend(page_data["results"])
    print(f"Page {page}/{pages_to_fetch} récupérée.")

api_data["results"] = all_results
api_data["pages_fetched"] = pages_to_fetch
api_data["api_total_pages"] = api_total_pages
api_data["has_more_pages"] = pages_to_fetch < api_total_pages

output_dir = Path(__file__).resolve().parents[2] / "data" / "raw"
output_dir.mkdir(parents=True, exist_ok=True)
output_file = output_dir / "movies_API.json"
temporary_file = output_file.with_suffix(".json.tmp")
temporary_file.write_text(
    json.dumps(api_data, indent=2, ensure_ascii=False),
    encoding="utf-8",
)
temporary_file.replace(output_file)

print(f"Extraction enregistrée dans : {output_file}")
print(f"Pages récupérées : {pages_to_fetch}/{api_total_pages}")
print(f"Films récupérés : {len(all_results)}")
if api_data["has_more_pages"]:
    print(
        f"L'API annonce {api_total_pages} pages, mais la pagination est limitée "
        f"à {max_api_page} pages."
    )
