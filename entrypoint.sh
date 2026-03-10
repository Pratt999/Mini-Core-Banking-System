#!/bin/bash
set -e

echo "[STARTUP] Initializing database..."
# Run the init-db command. Ignore errors if it's already initialized but create_all is idempotent.
flask init-db || echo "[STARTUP] Database initialization skipped or already done."

echo "[STARTUP] Starting Supervisor..."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
