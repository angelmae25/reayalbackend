# =============================================================================
# app/__init__.py  —  Flask application factory
# =============================================================================

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from .config import Config

db      = SQLAlchemy()
bcrypt  = Bcrypt()
jwt     = JWTManager()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # ── Extensions ────────────────────────────────────────────────────────────
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # ── Blueprints ────────────────────────────────────────────────────────────
    from .routes.auth       import auth_bp
    from .routes.news       import news_bp
    from .routes.events     import events_bp
    from .routes.clubs      import clubs_bp
    from .routes.marketplace import marketplace_bp
    from .routes.lost_found import lost_found_bp
    from .routes.chat       import chat_bp
    from .routes.leaderboard import leaderboard_bp
    from .routes.students   import students_bp

    app.register_blueprint(auth_bp,        url_prefix='/api/mobile/auth')
    app.register_blueprint(news_bp,        url_prefix='/api/mobile/news')
    app.register_blueprint(events_bp,      url_prefix='/api/mobile/events')
    app.register_blueprint(clubs_bp,       url_prefix='/api/mobile/clubs')
    app.register_blueprint(marketplace_bp, url_prefix='/api/mobile/marketplace')
    app.register_blueprint(lost_found_bp,  url_prefix='/api/mobile/lost-found')
    app.register_blueprint(chat_bp,        url_prefix='/api/mobile/chat')
    app.register_blueprint(leaderboard_bp, url_prefix='/api/mobile/leaderboard')
    app.register_blueprint(students_bp,    url_prefix='/api/mobile/students')

    # ── Health check ──────────────────────────────────────────────────────────
    @app.route('/api/mobile/ping')
    def ping():
        return {'status': 'ok', 'message': 'Scholife API is running'}

    return app
