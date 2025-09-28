"""
Initializes and exports all Flask extensions for the application.
This file breaks the circular import problem by providing a central,
app-independent place to instantiate extensions.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_smorest import Api
from flask_apscheduler import APScheduler

db = SQLAlchemy()
jwt = JWTManager()
scheduler = APScheduler()
api = Api()
# Disable the automatic "Default error response" in Swagger UI.
api.DEFAULT_ERROR_RESPONSE_NAME = None
