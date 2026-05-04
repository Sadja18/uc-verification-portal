import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Initialize extensions globally so they can be imported elsewhere (like models.py)
db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    """Application Factory Pattern"""
    app = Flask(__name__)
    
    # Configuration
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SECRET_KEY'] = 'dev-key-rusa-pmusha-2026' # Change for production
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, '../uc_audit.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions with the app instance
    db.init_app(app)
    login_manager.init_app(app)
    
    # Set the login view for @login_required decorators
    login_manager.login_view = 'auth.login'

    # Register Blueprints (Placeholder for Phase 3 & 4)
    # from .routes.auth import auth as auth_blueprint
    # app.register_blueprint(auth_blueprint)
    
    # from .routes.verifier import verifier as verifier_blueprint
    # app.register_blueprint(verifier_blueprint)

    return app