# =============================================================================
# app/routes/students.py  —  /api/mobile/students
# GET  /profile  — own profile
# PUT  /profile  — update contact / avatar / course / year_level. hoy
# =============================================================================

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import DataError
from .. import db
from ..models.models import Student

students_bp = Blueprint('students', __name__)


@students_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    student_id = int(get_jwt_identity())
    student    = Student.query.get_or_404(student_id)
    return jsonify(student.to_dict()), 200


@students_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    student_id = int(get_jwt_identity())
    student    = Student.query.get_or_404(student_id)
    data       = request.get_json(force=True, silent=True) or {}

    try:
        # Only update fields that were actually sent
        if 'contact' in data:
            student.contact    = data['contact']
        if 'course' in data:
            student.course     = data['course']
        if 'year_level' in data:
            student.year_level = data['year_level']
        if 'avatar_url' in data:
            # empty string means remove avatar
            student.avatar_url = data['avatar_url'] or None

        db.session.commit()
        return jsonify(student.to_dict()), 200

    except DataError:
        db.session.rollback()
        return jsonify({
            'message': 'Avatar too large. '
                       'Run: ALTER TABLE students MODIFY COLUMN avatar_url LONGTEXT;'
        }), 500

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Update failed: {str(e)}'}), 500