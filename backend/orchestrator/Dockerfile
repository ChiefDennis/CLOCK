FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# ADDED: Make the new entrypoint script executable.
RUN chmod +x /app/entrypoint.sh

EXPOSE 5000

# CHANGED: The container's command is now our shell script.
CMD ["/app/entrypoint.sh"]