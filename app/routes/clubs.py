# =============================================================================
# app/routes/clubs.py  —  /api/mobile/clubs
# GET  /                — list all clubs (with is_joined flag)
# GET  /<id>            — single club
# POST /<id>/join       — join a club
# POST /<id>/leave      — leave a club
# GET  /organizations   — list Spring Boot orgs as clubs (read-only) ← NEW
# =============================================================================

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import text
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


# ─────────────────────────────────────────────────────────────────────────────
# ORGANIZATIONS AS CLUBS  ← NEW
# GET /api/mobile/clubs/organizations
# Returns organizations created by the Spring Boot admin dashboard
# as club-formatted objects so Flutter can display them in ClubsView.
# These are READ-ONLY — students cannot join/leave org-based clubs here.
# Joining is managed by the admin through role assignments.
# ─────────────────────────────────────────────────────────────────────────────
@clubs_bp.route('/organizations', methods=['GET'])
@jwt_required()
def list_orgs_as_clubs():
    try:
        result = db.session.execute(text(
            "SELECT id, name, acronym, type, description, status "
            "FROM organizations "
            "WHERE status = 'ACTIVE' "
            "ORDER BY name ASC"
        ))
        rows  = result.mappings().all()
        clubs = []
        for r in rows:
            # Use acronym initials as display id prefix to avoid
            # collision with actual clubs table ids
            clubs.append({
                'id':          f"org_{r['id']}",
                'name':        r['name']        or '',
                'acronym':     r['acronym']     or '',
                'department':  r['type']        or '',
                'description': r['description'] or '',
                'icon_name':   'groups',
                'color':       '#8B1A1A',
                'is_joined':   False,   # read-only, no join/leave
                'member_count': 0,
                'is_org':      True,    # Flutter can use this to hide Join button
            })
        return jsonify(clubs), 200

    except Exception as e:
        # organizations table may not exist in all environments
        print(f'[Clubs] Could not load organizations: {e}')
        return jsonify([]), 200