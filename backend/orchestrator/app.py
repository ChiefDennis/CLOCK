"""
This file contains the main application factory, create_app.
It's responsible for creating the Flask app instance, configuring it,
initializing extensions, and registering API blueprints.
"""
import os
from flask import Flask, g, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from flask_cors import CORS

# Import extensions from their central location
from extensions import db, jwt, api, scheduler

def create_app():
    """Application factory function."""
    app = Flask(__name__)

    # --- Load Configurations ---
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@"
        f"{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
    app.config["JWT_IDENTITY_CLAIM"] = "sub"
    app.config["API_TITLE"] = "Key Management API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/docs"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

    # --- Load mail settings ---
    app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER")
    app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
    app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS", "True")
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
    app.config["MAIL_RECIPIENT"] = os.getenv("MAIL_RECIPIENT")
    
    # --- Initialize Extensions ---
    db.init_app(app)
    jwt.init_app(app)
    api.init_app(app)

    # --- Try to fix CORS xd ---
    CORS(app)

    # --- Start Background Scheduler ---
    # It's important that the scheduler is initialized and started only once.
    if scheduler.state == 0: 
        scheduler.init_app(app)

        # REVISED: This single job now handles all key reconciliation.
        scheduler.add_job(
            id='SyncAllProvidersJob', 
            func='services.scheduler:sync_all_providers', 
            trigger='interval', 
            hours=1,
            misfire_grace_time=60,
            coalesce=True
        )

        # This job remains the same.
        scheduler.add_job(
            id='ExecuteActionsJob',
            func='services.scheduler:execute_pending_actions',
            trigger='interval',
            minutes=1,
            misfire_grace_time=30,
            coalesce=True
        )

        scheduler.start()

    # --- Configure OpenAPI/Swagger JWT Support ---
    api.spec.components.security_scheme("BearerAuth", {
        "type": "http", "scheme": "bearer", "bearerFormat": "JWT"
    })
    api.spec.options["security"] = [{"BearerAuth": []}]

    # --- Register Blueprints ---
    # Do this inside the factory to avoid circular imports.
    from routes.auth_routes import auth_bp
    from routes.key_routes import key_bp
    from routes.user_routes import user_bp
    from routes.admin_routes import admin_bp
    from routes.action_routes import action_bp

    api.register_blueprint(auth_bp)
    api.register_blueprint(key_bp)
    api.register_blueprint(user_bp)
    api.register_blueprint(admin_bp)
    api.register_blueprint(action_bp)

    # --- Register a 'before_request' hook ---
    # This function will run before every request to an API endpoint.
    @app.before_request
    def load_user_from_jwt():
        # A list of public endpoints that don't require a JWT.
        public_endpoints = ["auth.Login", "openapi.openapi_json", "openapi.openapi_ui"]
        
        # If the requested endpoint is not public, verify JWT and load user.
        if request.endpoint not in public_endpoints:
            try:
                verify_jwt_in_request()
                identity = get_jwt_identity()
                g.current_user = identity
                # To get the user role, we need the User model.
                from models import User
                user = User.query.filter_by(username=identity).first()
                g.current_role = user.role if user else None
            except Exception:
                g.current_user = None
                g.current_role = None
    return app