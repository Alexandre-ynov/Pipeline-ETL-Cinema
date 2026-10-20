import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, SchemaError


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_FILE = ROOT / "contracts" / "movies_API_contract.json"
DATA_FILE = ROOT / "data" / "raw" / "movies_API.json"


def main():
	with CONTRACT_FILE.open("r", encoding="utf-8") as file:
		schema = json.load(file)

	with DATA_FILE.open("r", encoding="utf-8") as file:
		payload = json.load(file)

	try:
		Draft202012Validator.check_schema(schema)
	except SchemaError as error:
		print(f"Contrat JSON Schema invalide : {error.message}")
		return 2

	validator = Draft202012Validator(schema)
	errors = sorted(
		validator.iter_errors(payload),
		key=lambda error: list(map(str, error.absolute_path)),
	)

	if errors:
		print(f"JSON invalide : {len(errors)} erreur(s) trouvée(s).")
		for error in errors[:20]:
			location = ".".join(map(str, error.absolute_path)) or "$"
			print(f"- {location}: {error.message}")
		if len(errors) > 20:
			print(f"... et {len(errors) - 20} autre(s) erreur(s).")
		return 1

	print(
		"JSON valide : "
		f"{len(payload['results'])} films conformes au contrat."
	)
	return 0


if __name__ == "__main__":
	sys.exit(main())