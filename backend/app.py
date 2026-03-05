import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from .config import Config
from .extensions import db, cache, migrate
from flask_jwt_extended import JWTManager
from .utils.errors import register_error_handlers


def create_app():
    load_dotenv()

    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)

    db.init_app(app)
    cache.init_app(app)
    migrate.init_app(app, db)

    jwt = JWTManager(app)

    from .routes.auth_routes import auth_bp
    from .routes.admin_routes import admin_bp
    from .routes.doctor_routes import doctor_bp
    from .routes.patient_routes import patient_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(doctor_bp, url_prefix="/doctor")
    app.register_blueprint(patient_bp, url_prefix="/patient")

    register_error_handlers(app)

    return app


app = create_app()
