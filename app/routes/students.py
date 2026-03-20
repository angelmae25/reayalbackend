# =============================================================================
# app/routes/students.py  —  /api/mobile/students
# GET  /profile        — own profile
# PUT  /profile        — update contact / avatar
# =============================================================================

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
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
    data       = request.get_json(silent=True) or {}

    student.contact    = data.get('contact',    student.contact)
    student.avatar_url = data.get('avatar_url', student.avatar_url)
    student.course     = data.get('course',     student.course)
    student.year_level = data.get('year_level', student.year_level)
    db.session.commit()
    return jsonify(student.to_dict()), 200
