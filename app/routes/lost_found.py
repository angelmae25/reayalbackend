# =============================================================================
# app/routes/lost_found.py  —  /api/mobile/lost-found
#
# FIXES:
#   1. report() now validates that `title` is non-empty (it was silently
#      accepting blank titles, producing broken cards in the UI).
#   2. report() validates that `status` is either 'lost' or 'found'.
#   3. update_item() now also allows updating the status (e.g. lost → found
#      when the item is recovered), which was missing.
#   4. update_item() permission check error message is more descriptive.
# =============================================================================

from datetime import date
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import DataError, OperationalError
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
    data       = request.get_json(force=True, silent=True)

    if not data:
        return jsonify({'message': 'Invalid or missing JSON body.'}), 400

    # FIX: validate title
    title = data.get('title', '').strip()
    if not title:
        return jsonify({'message': 'Title is required.'}), 400

    # FIX: validate status value
    status = data.get('status', 'lost')
    if status not in ('lost', 'found'):
        return jsonify({'message': 'status must be "lost" or "found".'}), 400

    # Parse date — default to today if not provided
    raw_date = data.get('date', date.today().isoformat())
    try:
        item_date = date.fromisoformat(raw_date)
    except ValueError:
        return jsonify({'message': 'date must be in YYYY-MM-DD format.'}), 400

    try:
        item = LostFound(
            title       = title,
            description = data.get('description', ''),
            location    = data.get('location', ''),
            date        = item_date,
            status      = status,
            reporter_id = student_id,
            image_url   = data.get('image_url'),
        )
        db.session.add(item)
        db.session.commit()
        return jsonify(item.to_dict()), 201

    except DataError:
        db.session.rollback()
        return jsonify({
            'message': 'Image too large for the database. '
                       'Run: ALTER TABLE lost_found MODIFY COLUMN image_url LONGTEXT;'
        }), 500

    except OperationalError as e:
        db.session.rollback()
        return jsonify({'message': f'Database error: {str(e)}'}), 500

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Unexpected error: {str(e)}'}), 500


@lost_found_bp.route('/<int:item_id>', methods=['PUT'])
@jwt_required()
def update_item(item_id):
    student_id = int(get_jwt_identity())
    item = LostFound.query.get_or_404(item_id)

    if item.reporter_id != student_id:
        return jsonify({'message': 'You can only edit your own reports.'}), 403

    data = request.get_json(force=True, silent=True) or {}

    if 'is_resolved' in data:
        item.is_resolved = bool(data['is_resolved'])

    if 'description' in data:
        item.description = data['description']

    # FIX: allow status change (e.g. mark a lost item as found)
    if 'status' in data:
        new_status = data['status']
        if new_status not in ('lost', 'found'):
            return jsonify({'message': 'status must be "lost" or "found".'}), 400
        item.status = new_status

    db.session.commit()
    return jsonify(item.to_dict()), 200