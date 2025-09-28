# /modules/gcp/app.py
from flask import Flask
from routes.gcp_internal_routes import gcp_bp

app = Flask(__name__)
app.register_blueprint(gcp_bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)