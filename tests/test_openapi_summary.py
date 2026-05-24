import json
import subprocess
import sys
from pathlib import Path


def test_openapi_summary_script_outputs_core_metadata(tmp_path: Path):
    openapi = {
        "info": {
            "title": "ProPlus API",
            "version": "1.0.0-phase1",
            "description": "Test description",
        },
        "tags": [
            {"name": "system", "description": "System endpoints"},
            {"name": "auth", "description": "Auth endpoints"},
        ],
        "paths": {
            "/healthz": {
                "get": {
                    "tags": ["system"],
                    "summary": "Liveness check",
                }
            }
        },
    }

    path = tmp_path / "openapi.json"
    path.write_text(json.dumps(openapi))

    result = subprocess.run(
        [sys.executable, "scripts/openapi_summary.py", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "title: ProPlus API" in result.stdout
    assert "version: 1.0.0-phase1" in result.stdout
    assert "description: True" in result.stdout
    assert "GET     /healthz" in result.stdout
    assert "summary=Liveness check" in result.stdout
