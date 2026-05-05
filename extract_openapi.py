import json
from main import app # Importa la tua istanza FastAPI dal file principale

def save_openapi():
    # Estrae lo schema OpenAPI generato da FastAPI
    openapi_schema = app.openapi()
    with open("openapi.json", "w") as f:
        json.dump(openapi_schema, f, indent=2)
    print("✅ File openapi.json generato con successo!")

if __name__ == "__main__":
    save_openapi()