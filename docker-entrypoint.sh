#!/bin/sh
set -e

# Wait for MySQL to be ready before starting Flask
if [ -n "$DB_HOST" ]; then
  echo "Waiting for MySQL at $DB_HOST..."
  python "$(dirname "$0")/wait_for_db.py"
  echo "MySQL is up."
fi

exec "$@"
