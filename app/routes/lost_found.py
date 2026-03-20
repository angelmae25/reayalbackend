# =============================================================================
# app/routes/lost_found.py  —  /api/mobile/lost-found
# GET  /         — list (optional ?status=lost|found)
# GET  /<id>     — single
# POST /         — report
# PUT  /<id>     — update / resolve
# =============================================================================

from datetime import date
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .. import db
from ..models.models import LostFound

lost_found_bp = Blueprint('lost_found', __name__)


@lost_found_bp.route('/', methods=['GET'])
@jwt_required()
def list_items():
    status = request.args.get('status')
    query  = LostFound.query.order_by(LostFound.created_at.desc())
    if status in ('lost', 'found'):
        query = query.filter_by(status=status)
    items = query.all()
    return jsonify([i.to_dict() for i in items]), 200


@lost_found_bp.route('/<int:item_id>', methods=['GET'])
@jwt_required()
def get_item(item_id):
    item = LostFound.query.get_or_404(item_id)
    return jsonify(item.to_dict()), 200


@lost_found_bp.route('/', methods=['POST'])
@jwt_required()
def report():
    student_id = int(get_jwt_identity())
    data       = request.get_json(silent=True) or {}

    item = LostFound(
        title       = data.get('title', ''),
        description = data.get('description'),
        location    = data.get('location', ''),
        date        = date.fromisoformat(data.get('date', date.today().isoformat())),
        status      = data.get('status', 'lost'),
        reporter_id = student_id,
        image_url   = data.get('image_url'),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201


@lost_found_bp.route('/<int:item_id>', methods=['PUT'])
@jwt_required()
def update_item(item_id):
    student_id = int(get_jwt_identity())
    item = LostFound.query.get_or_404(item_id)
    if item.reporter_id != student_id:
        return jsonify({'message': 'Forbidden'}), 403

    data = request.get_json(silent=True) or {}
    item.is_resolved = data.get('is_resolved', item.is_resolved)
    item.description = data.get('description', item.description)
    db.session.commit()
    return jsonify(item.to_dict()), 200
