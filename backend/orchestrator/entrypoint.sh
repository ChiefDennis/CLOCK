#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -x 
set -e

# Run the Python script to wait for the DB and initialize it.
echo "--- Running database setup from entrypoint.py ---"
python entrypoint.py

# Now that the setup is done, start the Gunicorn server as the main process.
# 'exec' replaces the shell process with the Gunicorn process.
echo "--- Starting Gunicorn server ---"
exec gunicorn --bind 0.0.0.0:5000 --workers=3 --preload "app:create_app()"