# =============================================================================
# app/routes/students.py  —  /api/mobile/students
# GET  /profile  — own profile (with rank, club_count, post_count)
# PUT  /profile  — update contact / avatar / course / year_level
#
# FIX: post_count query wrapped in try/except because the `news` table
#      may not have a `student_id` column yet. Returns 0 instead of 500.
# =============================================================================

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import text
from sqlalchemy.exc import DataError
from .. import db
from ..models.models import Student

students_bp = Blueprint('students', __name__)


# ── HELPER: safely count rows, returns 0 on any SQL error ────────────────────
def _safe_count(sql: str, params: dict) -> int:
    """Execute a COUNT query; return 0 if the column/table doesn't exist yet."""
    try:
        return db.session.execute(text(sql), params).scalar() or 0
    except Exception:
        db.session.rollback()
        return 0


# ── GET /profile ──────────────────────────────────────────────────────────────
@students_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    student_id = int(get_jwt_identity())
    student    = Student.query.get_or_404(student_id)

    # Rank = students with MORE points + 1
    rank = _safe_count(
        "SELECT COUNT(*) + 1 FROM students WHERE points > :pts AND status = 'ACTIVE'",
        {'pts': student.points or 0}
    ) or 1

    # Clubs this student has joined
    club_count = _safe_count(
        "SELECT COUNT(*) FROM club_memberships WHERE student_id = :sid",
        {'sid': student_id}
    )

    # News articles posted by this student
    # NOTE: if your `news` table uses a different column (e.g. author_id),
    # change `student_id` below to match your actual schema.
    post_count = _safe_count(
        "SELECT COUNT(*) FROM news WHERE student_id = :sid",
        {'sid': student_id}
    )

    return jsonify({
        'id':         str(student.id),
        'full_name':  student.full_name,
        'email':      student.email,
        'student_id': student.student_id,
        'course':     student.course     or '',
        'year_level': student.year_level or '',
        'department': student.department or '',
        'contact':    student.contact    or None,
        'points':     student.points     or 0,
        'avatar_url': student.avatar_url or None,
        'rank':       rank,
        'club_count': club_count,
        'post_count': post_count,
    }), 200


# ── PUT /profile ──────────────────────────────────────────────────────────────
@students_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    student_id = int(get_jwt_identity())
    student    = Student.query.get_or_404(student_id)
    data       = request.get_json(force=True, silent=True) or {}

    try:
        if 'contact' in data:
            student.contact    = data['contact']
        if 'course' in data:
            student.course     = data['course']
        if 'year_level' in data:
            student.year_level = data['year_level']
        if 'avatar_url' in data:
            student.avatar_url = data['avatar_url'] or None

        db.session.commit()

        rank = _safe_count(
            "SELECT COUNT(*) + 1 FROM students WHERE points > :pts AND status = 'ACTIVE'",
            {'pts': student.points or 0}
        ) or 1

        club_count = _safe_count(
            "SELECT COUNT(*) FROM club_memberships WHERE student_id = :sid",
            {'sid': student_id}
        )

        post_count = _safe_count(
            "SELECT COUNT(*) FROM news WHERE student_id = :sid",
            {'sid': student_id}
        )

        return jsonify({
            'id':         str(student.id),
            'full_name':  student.full_name,
            'email':      student.email,
            'student_id': student.student_id,
            'course':     student.course     or '',
            'year_level': student.year_level or '',
            'department': student.department or '',
            'contact':    student.contact    or None,
            'points':     student.points     or 0,
            'avatar_url': student.avatar_url or None,
            'rank':       rank,
            'club_count': club_count,
            'post_count': post_count,
        }), 200

    except DataError:
        db.session.rollback()
        return jsonify({
            'message': 'Avatar too large. '
                       'Run: ALTER TABLE students MODIFY COLUMN avatar_url LONGTEXT;'
        }), 500

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Update failed: {str(e)}'}), 500