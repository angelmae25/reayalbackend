# =============================================================================
# app/__init__.py  —  Flask application factory
# =============================================================================

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_socketio import SocketIO
from .config import Config

# ── Extensions ───────────────────────────────────────────────────────────────
db       = SQLAlchemy()
bcrypt   = Bcrypt()
jwt      = JWTManager()
socketio = SocketIO(cors_allowed_origins="*", async_mode='threading')


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # ── Initialize extensions ─────────────────────────────────────────────────
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    socketio.init_app(app, async_mode='threading')
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # ── Global error handlers ─────────────────────────────────────────────────
    @app.errorhandler(413)
    def too_large(e):
        return jsonify({'message': 'Image is too large. Please use a smaller photo (max 10 MB).'}), 413

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({'message': 'Bad request. Please check your input.'}), 400

    # ── Blueprints ────────────────────────────────────────────────────────────
    from .routes.auth        import auth_bp
    from .routes.news        import news_bp
    from .routes.events      import events_bp
    from .routes.clubs       import clubs_bp
    from .routes.marketplace import marketplace_bp
    from .routes.lost_found  import lost_found_bp
    from .routes.chat        import chat_bp
    from .routes.leaderboard import leaderboard_bp
    from .routes.students    import students_bp
    from .routes.reports     import reports_bp
    from .routes.org_post    import org_posts_bp

    app.register_blueprint(auth_bp,        url_prefix='/api/mobile/auth')
    app.register_blueprint(news_bp,        url_prefix='/api/mobile/news')
    app.register_blueprint(events_bp,      url_prefix='/api/mobile/events')
    app.register_blueprint(clubs_bp,       url_prefix='/api/mobile/clubs')
    app.register_blueprint(marketplace_bp, url_prefix='/api/mobile/marketplace')
    app.register_blueprint(lost_found_bp,  url_prefix='/api/mobile/lost-found')
    app.register_blueprint(chat_bp,        url_prefix='/api/mobile/chat')
    app.register_blueprint(leaderboard_bp, url_prefix='/api/mobile/leaderboard')
    app.register_blueprint(students_bp,    url_prefix='/api/mobile/students')
    app.register_blueprint(reports_bp,     url_prefix='/api/mobile/reports')
    app.register_blueprint(org_posts_bp, url_prefix='/api/mobile')

    # ── Register Socket.IO event handlers ────────────────────────────────────
    from .routes.chat_socket import register_socket_events
    register_socket_events(socketio)

    # ── Health check ──────────────────────────────────────────────────────────
    @app.route('/api/mobile/ping')
    def ping():
        return {'status': 'ok', 'message': 'Scholife API is running'}

    return app