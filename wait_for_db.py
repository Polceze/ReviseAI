"""
Blocks until MySQL is reachable and accepting authenticated connections,
or exits with an error after a timeout.

Uses mysql-connector-python (already in requirements.txt) instead of the
`mysqladmin` CLI, because the Debian `default-mysql-client` package is the
MariaDB client and cannot authenticate against MySQL 8's default
caching_sha2_password plugin.
"""
import os
import sys
import time

import mysql.connector
from mysql.connector import Error

DB_HOST = os.environ.get("DB_HOST")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_NAME = os.environ.get("DB_NAME")

MAX_ATTEMPTS = 60
SLEEP_SECONDS = 2

last_error = None
for attempt in range(1, MAX_ATTEMPTS + 1):
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            connection_timeout=3,
        )
        conn.close()
        sys.exit(0)
    except Error as e:
        last_error = e
        time.sleep(SLEEP_SECONDS)

print(f"MySQL did not become ready in time. Last error: {last_error}")
sys.exit(1)
