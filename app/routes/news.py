# =============================================================================
# app/routes/news.py  —  /api/mobile/news
# FIXES:
#   1. POST / now requires a role assignment (org officer only)
#   2. POST / now stores organization_id and author_name from the student
#   3. Added DELETE /<id> so org officers can remove their own posts
# =============================================================================

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .. import db
from ..models.models import Student, News, RoleAssignment

news_bp = Blueprint('news', __name__)


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: Resolve which organization this student may post under.
# Accepts optional ?org_id= query param; falls back to their first assignment.
# Returns (org_id, author_name) or raises ValueError with a user-friendly msg.
# ─────────────────────────────────────────────────────────────────────────────
def _resolve_org(student: Student, requested_org_id: int | None):
    assignments = RoleAssignment.query.filter_by(student_id=student.id).all()
    if not assignments:
        raise ValueError('You do not have a role in any organization and cannot post.')

    org_ids = {a.organization_id for a in assignments}

    if requested_org_id is not None:
        if requested_org_id not in org_ids:
            raise ValueError('You are not an officer of the requested organization.')
        org_id = requested_org_id
    else:
        org_id = assignments[0].organization_id  # default to first

    # Build author label: "<RoleName> · <OrgName>"
    chosen = next(a for a in assignments if a.organization_id == org_id)
    author = f"{chosen.role_name} · {chosen.organization.name}"
    return org_id, author


# ─────────────────────────────────────────────────────────────────────────────
# GET /  — list all news (optional ?category=health)
# ─────────────────────────────────────────────────────────────────────────────
@news_bp.route('/', methods=['GET'])
@jwt_required()
def list_news():
    category = request.args.get('category', 'all')
    query = News.query.order_by(News.published_at.desc())

    if category and category != 'all':
        query = query.filter_by(category=category)

    articles = query.all()
    return jsonify([a.to_dict() for a in articles]), 200


# ─────────────────────────────────────────────────────────────────────────────
# GET /<id>  — single article
# ─────────────────────────────────────────────────────────────────────────────
@news_bp.route('/<int:news_id>', methods=['GET'])
@jwt_required()
def get_news(news_id):
    article = News.query.get_or_404(news_id)
    return jsonify(article.to_dict()), 200


# ─────────────────────────────────────────────────────────────────────────────
# POST /  — create news (ROLE REQUIRED)
# Body: { title, body, category, is_featured?, organization_id? }
# ─────────────────────────────────────────────────────────────────────────────
@news_bp.route('/', methods=['POST'])
@jwt_required()
def create_news():
    student_id = int(get_jwt_identity())
    student = Student.query.get_or_404(student_id)

    data = request.get_json(silent=True) or {}

    # Validate required fields
    if not data.get('title', '').strip():
        return jsonify({'message': 'title is required.'}), 400
    if not data.get('body', '').strip():
        return jsonify({'message': 'body is required.'}), 400

    # Resolve org assignment — rejects if student has no role
    requested_org_id = data.get('organization_id')
    try:
        org_id, author_name = _resolve_org(
            student,
            int(requested_org_id) if requested_org_id else None
        )
    except ValueError as e:
        return jsonify({'message': str(e)}), 403

    article = News(
        title           = data['title'].strip(),
        body            = data['body'].strip(),
        category        = data.get('category', 'all'),
        is_featured     = bool(data.get('is_featured', False)),
        image_url       = data.get('image_url'),
        author_name     = author_name,
        organization_id = org_id,
    )
    db.session.add(article)
    db.session.commit()
    return jsonify(article.to_dict()), 201


# ─────────────────────────────────────────────────────────────────────────────
# DELETE /<id>  — delete news (only the posting org's officer may delete)
# ─────────────────────────────────────────────────────────────────────────────
@news_bp.route('/<int:news_id>', methods=['DELETE'])
@jwt_required()
def delete_news(news_id):
    student_id = int(get_jwt_identity())
    student = Student.query.get_or_404(student_id)
    article = News.query.get_or_404(news_id)

    # Verify the student has a role in the org that owns this article
    if article.organization_id is None:
        return jsonify({'message': 'This article cannot be deleted from the mobile app.'}), 403

    has_role = RoleAssignment.query.filter_by(
        student_id=student.id,
        organization_id=article.organization_id
    ).first()

    if not has_role:
        return jsonify({'message': 'You do not have permission to delete this article.'}), 403

    db.session.delete(article)
    db.session.commit()
    return jsonify({'message': 'Article deleted.'}), 200