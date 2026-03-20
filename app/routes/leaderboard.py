# =============================================================================
# app/routes/leaderboard.py  —  /api/mobile/leaderboard
# =============================================================================

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import text
from .. import db
from ..models.models import Student

leaderboard_bp = Blueprint('leaderboard', __name__)


@leaderboard_bp.route('/', methods=['GET'])
@jwt_required()
def get_leaderboard():
    # Use the leaderboard VIEW defined in the SQL schema
    try:
        result = db.session.execute(text(
            "SELECT id, full_name, year_level, course, points, avatar_url, `rank` "
            "FROM leaderboard ORDER BY `rank` ASC LIMIT 50"
        ))
        rows = result.mappings().all()
        return jsonify([dict(r) for r in rows]), 200
    except Exception:
        # Fallback: manual rank using Python if the view isn't available
        students = Student.query.filter_by(status='ACTIVE') \
                                .order_by(Student.points.desc()).limit(50).all()
        data = []
        for i, s in enumerate(students, 1):
            data.append({
                'id':         s.id,
                'full_name':  s.full_name,
                'year_level': s.year_level,
                'course':     s.course,
                'points':     s.points,
                'avatar_url': s.avatar_url,
                'rank':       i,
            })
        return jsonify(data), 200
