"""Export FastAPI OpenAPI schema to shared/openapi/eventforge-api.yaml."""

from __future__ import annotations

from pathlib import Path

import yaml

from eventforge.main import app

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "shared" / "openapi" / "eventforge-api.yaml"


def main() -> None:
    schema = app.openapi()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        yaml.dump(schema, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
