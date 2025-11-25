from flask import jsonify
from werkzeug.exceptions import HTTPException, BadRequest
from flask_jwt_extended.exceptions import JWTExtendedException

def register_error_handlers(app):

    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        return jsonify({
            "error": e.name,
            "message": e.description,
            "code": e.code
        }), e.code

    @app.errorhandler(BadRequest)
    def handle_bad_request(e):
        return jsonify({
            "error": "Bad Request",
            "message": "Invalid or malformed JSON body",
            "code": 400
        }), 400

    @app.errorhandler(JWTExtendedException)
    def handle_jwt_errors(e):
        return jsonify({
            "error": "Authentication Error",
            "message": str(e),
            "code": 401
        }), 401

    @app.errorhandler(Exception)
    def handle_general_exception(e):
        return jsonify({
            "error": "Internal Server Error",
            "message": str(e),
            "code": 500
        }), 500
