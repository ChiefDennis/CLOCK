# /orchestrator/entrypoint.py

"""
This script serves as the main entrypoint for the application, particularly in a
containerized environment. It performs the following setup tasks in order:
1. Waits for the PostgreSQL database to become available.
2. Creates a Flask application instance.
3. Initializes the database by creating all necessary tables and seeding them
   with default data, such as admin users and initial module statuses.

This ensures that the application environment is fully prepared before the main
service (e.g., a Gunicorn server) starts handling requests.
"""

import os
import time
import psycopg2
from app import create_app
from extensions import db
from models import User, ModuleStatus

def wait_for_postgres():
    """
    Blocks execution by polling the PostgreSQL database until it's ready to accept connections.

    This is crucial in environments like Docker Compose, where the application container might
    start before the database container is fully initialized. It attempts to connect in a loop,
    waiting one second between failed attempts.
    """
    while True:
        try:
            # Attempt to connect to the database using credentials from environment variables.
            conn = psycopg2.connect(
                dbname=os.getenv("POSTGRES_DB"),
                user=os.getenv("POSTGRES_USER"),
                password=os.getenv("POSTGRES_PASSWORD"),
                host=os.getenv("POSTGRES_HOST"),
                port=os.getenv("POSTGRES_PORT")
            )
            # If connection succeeds, close it and break the loop.
            conn.close()
            print("PostgreSQL is ready.")
            break
        except psycopg2.OperationalError:
            # If the connection fails (e.g., database is not ready), print a message and wait.
            print("Waiting for PostgreSQL...")
            time.sleep(1)

def initialize_db(app):
    """
    Initializes the database by creating tables and seeding them with default data.

    This function operates within the Flask application context to ensure access to the
    database extension and configuration.

    Args:
        app: The Flask application instance.
    """
    # Establish an application context to work with the database.
    with app.app_context():
        # Create all tables defined in the SQLAlchemy models.
        db.create_all()
        
        # --- Seed Default Users ---
        # Check if the default admin user already exists to prevent duplication.
        if not User.query.filter_by(username="admin").first():
            print("Creating default users...")
            
            # Create an admin user with the role 'admin'.
            admin = User(username="admin", role="admin", enabled=True)
            admin.set_password("admin") # It's recommended to change this default password.
            
            # Create a standard user with the role 'user'.
            user = User(username="user", role="user", enabled=True)
            user.set_password("user") # It's recommended to change this default password.
            
            # Add the new users to the session and commit them to the database.
            db.session.add(admin)
            db.session.add(user)
            db.session.commit()
        
        # --- Seed Module Statuses ---
        # Define the list of cloud provider modules to be managed.
        providers = ["aws", "gcp", "azure"]
        # Iterate through each provider to set its initial status.
        for provider in providers:
            # Check if a status entry for the provider already exists.
            if not ModuleStatus.query.filter_by(provider_name=provider).first():
                print(f"Setting default status for module: {provider}")
                # Create a new status entry, enabling only AWS by default.
                if provider=="aws":
                    status = ModuleStatus(provider_name=provider, is_enabled=True)
                else:
                    status = ModuleStatus(provider_name=provider, is_enabled=False)
                db.session.add(status)
        
        # Commit all new module statuses to the database in a single transaction.
        db.session.commit()

# Main execution block. This runs only when the script is executed directly.
if __name__ == "__main__":
    # 1. Wait for the database to be online and ready.
    wait_for_postgres()
    
    # 2. Create the Flask application instance.
    app = create_app()
    
    # 3. Initialize the database schema and seed initial data.
    initialize_db(app)
    
    print("Database setup complete.")