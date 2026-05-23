#!/usr/bin/env python3
import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: scripts/openapi_summary.py /path/to/openapi.json")
        return 2

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"❌ OpenAPI file not found: {path}")
        return 1

    data = json.loads(path.read_text())

    info = data.get("info", {})
    print("title:", info.get("title"))
    print("version:", info.get("version"))
    print("description:", bool(info.get("description")))
    print("tags:", data.get("tags"))

    print()
    print("paths:")
    for route_path, methods in sorted(data.get("paths", {}).items()):
        for method, meta in sorted(methods.items()):
            print(
                f"{method.upper():7} {route_path:35} "
                f"tags={meta.get('tags')} summary={meta.get('summary')}"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
