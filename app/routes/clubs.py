# =============================================================================
# app/routes/clubs.py  —  /api/mobile/clubs
# GET  /           — list all clubs (with is_joined flag)
# GET  /<id>       — single club
# POST /<id>/join  — join a club
# POST /<id>/leave — leave a club
# =============================================================================

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .. import db
from ..models.models import Club, Student

clubs_bp = Blueprint('clubs', __name__)


@clubs_bp.route('/', methods=['GET'])
@jwt_required()
def list_clubs():
    student_id = int(get_jwt_identity())
    student    = Student.query.get(student_id)
    joined_ids = {c.id for c in student.memberships} if student else set()

    clubs = Club.query.order_by(Club.name).all()
    return jsonify([c.to_dict(is_joined=(c.id in joined_ids)) for c in clubs]), 200


@clubs_bp.route('/<int:club_id>', methods=['GET'])
@jwt_required()
def get_club(club_id):
    student_id = int(get_jwt_identity())
    student    = Student.query.get(student_id)
    club       = Club.query.get_or_404(club_id)
    is_joined  = club in (student.memberships if student else [])
    return jsonify(club.to_dict(is_joined=is_joined)), 200


@clubs_bp.route('/<int:club_id>/join', methods=['POST'])
@jwt_required()
def join_club(club_id):
    student_id = int(get_jwt_identity())
    student    = Student.query.get_or_404(student_id)
    club       = Club.query.get_or_404(club_id)

    if club not in student.memberships:
        student.memberships.append(club)
        db.session.commit()
    return jsonify({'message': f'Joined {club.name}', 'is_joined': True}), 200


@clubs_bp.route('/<int:club_id>/leave', methods=['POST'])
@jwt_required()
def leave_club(club_id):
    student_id = int(get_jwt_identity())
    student    = Student.query.get_or_404(student_id)
    club       = Club.query.get_or_404(club_id)

    if club in student.memberships:
        student.memberships.remove(club)
        db.session.commit()
    return jsonify({'message': f'Left {club.name}', 'is_joined': False}), 200
