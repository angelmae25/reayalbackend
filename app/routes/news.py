# =============================================================================
# app/routes/news.py  —  /api/mobile/news
# GET  /        — list all news (optional ?category=health)
# GET  /<id>    — single article
# POST /        — create (admin only in real app, open for now)
# =============================================================================

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from .. import db
from ..models.models import News

news_bp = Blueprint('news', __name__)


@news_bp.route('/', methods=['GET'])
@jwt_required()
def list_news():
    category = request.args.get('category', 'all')
    query    = News.query.order_by(News.published_at.desc())

    if category and category != 'all':
        query = query.filter_by(category=category)

    articles = query.all()
    return jsonify([a.to_dict() for a in articles]), 200


@news_bp.route('/<int:news_id>', methods=['GET'])
@jwt_required()
def get_news(news_id):
    article = News.query.get_or_404(news_id)
    return jsonify(article.to_dict()), 200


@news_bp.route('/', methods=['POST'])
@jwt_required()
def create_news():
    data = request.get_json(silent=True) or {}
    article = News(
        title       = data.get('title', ''),
        body        = data.get('body', ''),
        category    = data.get('category', 'all'),
        is_featured = data.get('is_featured', False),
        image_url   = data.get('image_url'),
        author_name = data.get('author_name', 'Scholife Editorial'),
    )
    db.session.add(article)
    db.session.commit()
    return jsonify(article.to_dict()), 201
