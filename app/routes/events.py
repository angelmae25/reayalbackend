# =============================================================================
# app/routes/events.py  —  /api/mobile/events
# =============================================================================

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from .. import db
from ..models.models import Event

events_bp = Blueprint('events', __name__)


@events_bp.route('/', methods=['GET'])
@jwt_required()
def list_events():
    events = Event.query.order_by(Event.date.asc()).all()
    return jsonify([e.to_dict() for e in events]), 200


@events_bp.route('/<int:event_id>', methods=['GET'])
@jwt_required()
def get_event(event_id):
    event = Event.query.get_or_404(event_id)
    return jsonify(event.to_dict()), 200


@events_bp.route('/', methods=['POST'])
@jwt_required()
def create_event():
    from datetime import date
    data  = request.get_json(silent=True) or {}
    event = Event(
        short_name  = data.get('short_name', ''),
        full_name   = data.get('full_name', ''),
        date        = date.fromisoformat(data.get('date', date.today().isoformat())),
        venue       = data.get('venue', ''),
        category    = data.get('category', 'General'),
        color       = data.get('color', '#8B1A1A'),
        description = data.get('description'),
    )
    db.session.add(event)
    db.session.commit()
    return jsonify(event.to_dict()), 201
