#!/bin/bash
set -euo pipefail

python manage.py check --deploy
python manage.py migrate --noinput
python manage.py collectstatic --noinput
(cd frontend && npm ci && npm run build)

echo "Build and database preparation completed. No deployment target is configured."
exit 1
