from flask import Flask, request, jsonify
from routes.aws_internal_routes import aws_bp
import boto3, os

app = Flask(__name__)

app.register_blueprint(aws_bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)