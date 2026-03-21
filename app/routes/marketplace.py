# =============================================================================
# app/routes/marketplace.py  —  /api/mobile/marketplace
# =============================================================================

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import DataError, OperationalError
from .. import db
from ..models.models import MarketplaceItem

marketplace_bp = Blueprint('marketplace', __name__)


@marketplace_bp.route('/', methods=['GET'])
@jwt_required()
def list_items():
    search = request.args.get('search', '').strip()
    query  = MarketplaceItem.query.filter_by(is_sold=False) \
                                  .order_by(MarketplaceItem.posted_at.desc())
    if search:
        query = query.filter(MarketplaceItem.name.ilike(f'%{search}%'))
    items = query.all()
    return jsonify([i.to_dict() for i in items]), 200


@marketplace_bp.route('/<int:item_id>', methods=['GET'])
@jwt_required()
def get_item(item_id):
    item = MarketplaceItem.query.get_or_404(item_id)
    return jsonify(item.to_dict()), 200


@marketplace_bp.route('/', methods=['POST'])
@jwt_required()
def create_item():
    student_id = int(get_jwt_identity())

    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({'message': 'Invalid or missing JSON body.'}), 400

    try:
        item = MarketplaceItem(
            name        = data.get('name', '').strip(),
            description = data.get('description', ''),
            condition_  = data.get('condition', 'Good condition'),
            price       = float(data.get('price', 0)),
            image_url   = data.get('image_url'),
            seller_id   = student_id,
        )
        db.session.add(item)
        db.session.commit()
        return jsonify(item.to_dict()), 201

    except DataError as e:
        db.session.rollback()
        # Most likely image_url column is still VARCHAR — needs migration
        return jsonify({
            'message': 'Database error: image column too small. '
                       'Run: ALTER TABLE marketplace_items MODIFY COLUMN image_url LONGTEXT;'
        }), 500

    except OperationalError as e:
        db.session.rollback()
        return jsonify({'message': f'Database connection error: {str(e)}'}), 500

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Unexpected error: {str(e)}'}), 500


@marketplace_bp.route('/<int:item_id>', methods=['PUT'])
@jwt_required()
def update_item(item_id):
    student_id = int(get_jwt_identity())
    item = MarketplaceItem.query.get_or_404(item_id)
    if item.seller_id != student_id:
        return jsonify({'message': 'Forbidden'}), 403

    data = request.get_json(force=True, silent=True) or {}
    item.name       = data.get('name',      item.name)
    item.condition_ = data.get('condition', item.condition_)
    item.price      = float(data.get('price', item.price))
    item.is_sold    = data.get('is_sold',   item.is_sold)
    db.session.commit()
    return jsonify(item.to_dict()), 200


@marketplace_bp.route('/<int:item_id>', methods=['DELETE'])
@jwt_required()
def delete_item(item_id):
    student_id = int(get_jwt_identity())
    item = MarketplaceItem.query.get_or_404(item_id)
    if item.seller_id != student_id:
        return jsonify({'message': 'Forbidden'}), 403
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Deleted'}), 200