# =============================================================================
# app/routes/marketplace.py  —  /api/mobile/marketplace
#
# FIXES:
#   1. create_item() now validates that `name` is non-empty before attempting
#      the DB insert (previously an empty name silently created a broken record).
#   2. create_item() validates that `price` is a non-negative number.
#   3. update_item() validates price is non-negative on edit.
#   4. create_item() strips whitespace from name to prevent blank-looking items.
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

    # FIX: validate name
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'message': 'Item name is required.'}), 400

    # FIX: validate price
    try:
        price = float(data.get('price', 0))
        if price < 0:
            return jsonify({'message': 'Price cannot be negative.'}), 400
    except (ValueError, TypeError):
        return jsonify({'message': 'Price must be a number.'}), 400

    try:
        item = MarketplaceItem(
            name        = name,
            description = data.get('description', ''),
            condition_  = data.get('condition', 'Good condition'),
            price       = price,
            image_url   = data.get('image_url'),
            seller_id   = student_id,
        )
        db.session.add(item)
        db.session.commit()
        return jsonify(item.to_dict()), 201

    except DataError:
        db.session.rollback()
        return jsonify({
            'message': 'Image too large for the database. '
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
        return jsonify({'message': 'You can only edit your own listings.'}), 403

    data = request.get_json(force=True, silent=True) or {}

    if 'name' in data:
        name = data['name'].strip()
        if not name:
            return jsonify({'message': 'Item name cannot be empty.'}), 400
        item.name = name

    if 'condition' in data:
        item.condition_ = data['condition']

    if 'price' in data:
        try:
            price = float(data['price'])
            if price < 0:
                return jsonify({'message': 'Price cannot be negative.'}), 400
            item.price = price
        except (ValueError, TypeError):
            return jsonify({'message': 'Price must be a number.'}), 400

    if 'is_sold' in data:
        item.is_sold = bool(data['is_sold'])

    db.session.commit()
    return jsonify(item.to_dict()), 200


@marketplace_bp.route('/<int:item_id>', methods=['DELETE'])
@jwt_required()
def delete_item(item_id):
    student_id = int(get_jwt_identity())
    item = MarketplaceItem.query.get_or_404(item_id)

    if item.seller_id != student_id:
        return jsonify({'message': 'You can only delete your own listings.'}), 403

    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Listing deleted.'}), 200