#!/usr/bin/env bash
set -e
python -c "import sys; print('Python:', sys.version)"
exec "$@"
