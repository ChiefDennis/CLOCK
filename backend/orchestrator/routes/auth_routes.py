from flask_smorest import Blueprint, abort
from flask.views import MethodView
from services.auth import generate_token, authenticate_user
from schemas.request_schemas import LoginSchema, TokenSchema
from schemas.error_schemas import ErrorSchema
from services.logger import log_request_response

# Create a Blueprint for auth routes with prefix /auth and description for Swagger
auth_bp = Blueprint("Auth", "auth", url_prefix="/auth", description="Authentication for the key management application")

@auth_bp.route("/login")
class Login(MethodView):
    @auth_bp.response(200, TokenSchema)
    @log_request_response("User Login Attempt", hide_request_fields=["password"], hide_response_body=True)
    @auth_bp.arguments(LoginSchema)
    def post(self, data):
        """
        Validates username and password, and returns a JWT if credentials are valid.
        """
        user = authenticate_user(data["username"], data["password"])
        
        if not user:
            abort(401, message="Invalid credentials.")
        
        # On success, generate and return the token.
        token = generate_token(user)
        return {"access_token": token}