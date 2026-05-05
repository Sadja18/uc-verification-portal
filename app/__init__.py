import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Initialize extensions globally
db = SQLAlchemy()
login_manager = LoginManager()

# Setup basic logging for the app
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_global_mpr(app):
    """
    Loads the Master MPR DataFrame into app.config['MASTER_DF'] on startup.
    This ensures the data is in memory and available to all requests.
    """
    with app.app_context():
        try:
            # Import locally to avoid circular imports if mpr_loader imports app
            from app.services.mpr_loader import (
                load_rusa_mpr,
                load_pmusha_mpr,
                harmonize_and_merge_mpr,
            )

            # Define paths - In production, these might come from config or env vars
            # For now, assuming they are in a 'data/master' folder relative to project root
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            rusa_path = os.path.join(base_dir, "data", "master", "RUSA_MPR_March.xlsx")
            print("rusa_path ", rusa_path)
            pmusha_path = os.path.join(
                base_dir, "data", "master", "PM_USHA_MPR_March.xlsx"
            )

            logger.info("Loading RUSA MPR...")
            df_rusa = load_rusa_mpr(rusa_path)

            logger.info("Loading PM-USHA MPR...")
            df_pmusha = load_pmusha_mpr(pmusha_path)

            logger.info("Harmonizing and Merging MPR Data...")
            master_df = harmonize_and_merge_mpr(df_rusa, df_pmusha)

            if master_df is not None and not master_df.empty:
                app.config["MASTER_DF"] = master_df
                logger.info(f"SUCCESS: Loaded {len(master_df)} projects into memory.")
            else:
                logger.error("FAILED: Master DataFrame is empty. Check source files.")
                app.config["MASTER_DF"] = None

        except Exception as e:
            logger.error(f"CRITICAL ERROR loading MPR data: {e}")
            app.config["MASTER_DF"] = None


def create_app():
    """Application Factory Pattern"""
    app = Flask(__name__)

    # Configuration
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config["SECRET_KEY"] = "dev-key-rusa-pmusha-2026"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
        basedir, "../uc_audit.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize extensions with the app instance
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # Load Master Data into Memory
    load_global_mpr(app)

    # Register Blueprints
    # We will create these files in the next steps
    from app.routes.verifier import verifier as verifier_blueprint

    app.register_blueprint(verifier_blueprint)

    from app.routes.auth import auth as auth_blueprint

    app.register_blueprint(auth_blueprint)

    return app


@login_manager.user_loader
def load_user(user_id):
    """Callback for Flask-Login to load a user by ID."""
    from app.models import User

    return User.query.get(int(user_id))


# import os
# from flask import Flask
# from flask_sqlalchemy import SQLAlchemy
# from flask_login import LoginManager

# # Initialize extensions globally so they can be imported elsewhere (like models.py)
# db = SQLAlchemy()
# login_manager = LoginManager()

# def create_app():
#     """Application Factory Pattern"""
#     app = Flask(__name__)

#     # Configuration
#     basedir = os.path.abspath(os.path.dirname(__file__))
#     app.config['SECRET_KEY'] = 'dev-key-rusa-pmusha-2026' # Change for production
#     app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, '../uc_audit.db')
#     app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#     # Initialize extensions with the app instance
#     db.init_app(app)
#     login_manager.init_app(app)

#     # Set the login view for @login_required decorators
#     login_manager.login_view = 'auth.login'

#     # Register Blueprints (Placeholder for Phase 3 & 4)
#     # from .routes.auth import auth as auth_blueprint
#     # app.register_blueprint(auth_blueprint)

#     # from .routes.verifier import verifier as verifier_blueprint
#     # app.register_blueprint(verifier_blueprint)

#     return app
