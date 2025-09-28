# /modules/azure/app.py
from flask import Flask
from routes.azure_internal_routes import azure_bp

app = Flask(__name__)
app.register_blueprint(azure_bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)