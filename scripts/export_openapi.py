"""Script para exportar el esquema OpenAPI a un archivo JSON."""

import json
import os
import sys

# Añade el directorio raíz al path para importar la app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Necesitas las variables de entorno para instanciar settings
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
os.environ.setdefault("SECRET_KEY", "export-script-dummy-key")
os.environ.setdefault("APP_ENV", "development")

from app.main import app  # noqa: E402

schema = app.openapi()
output_path = "docs/openapi.json"

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(schema, f, indent=2, ensure_ascii=False)

print(f"   OpenAPI schema exported to {output_path}")
print(f"   Endpoints: {len(schema.get('paths', {}))}")
print(f"   Schemas: {len(schema.get('components', {}).get('schemas', {}))}")
