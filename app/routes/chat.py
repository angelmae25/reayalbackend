# =============================================================================
# app/routes/chat.py  —  /api/mobile/chat
# GET  /conversations              — my conversations
# POST /conversations              — start a new conversation
# GET  /conversations/<id>/messages — messages in a conversation
# POST /conversations/<id>/messages — send a message
# =============================================================================

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .. import db
from ..models.models import Conversation, Message, Student

chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/conversations', methods=['GET'])
@jwt_required()
def list_conversations():
    student_id = int(get_jwt_identity())
    student    = Student.query.get_or_404(student_id)
    convs      = student.conversations
    return jsonify([c.to_dict(student_id) for c in convs]), 200


@chat_bp.route('/conversations', methods=['POST'])
@jwt_required()
def create_conversation():
    student_id  = int(get_jwt_identity())
    data        = request.get_json(silent=True) or {}
    other_ids   = data.get('member_ids', [])   # list of student IDs
    is_group    = data.get('is_group', False)
    name        = data.get('name')

    conv = Conversation(name=name, is_group=is_group)
    db.session.add(conv)

    me = Student.query.get(student_id)
    conv.members.append(me)
    for oid in other_ids:
        other = Student.query.get(oid)
        if other:
            conv.members.append(other)

    db.session.commit()
    return jsonify(conv.to_dict(student_id)), 201


@chat_bp.route('/conversations/<int:conv_id>/messages', methods=['GET'])
@jwt_required()
def get_messages(conv_id):
    student_id = int(get_jwt_identity())
    conv       = Conversation.query.get_or_404(conv_id)
    msgs       = Message.query.filter_by(conversation_id=conv_id) \
                              .order_by(Message.sent_at.asc()).all()
    return jsonify([m.to_dict(student_id) for m in msgs]), 200


@chat_bp.route('/conversations/<int:conv_id>/messages', methods=['POST'])
@jwt_required()
def send_message(conv_id):
    student_id = int(get_jwt_identity())
    data       = request.get_json(silent=True) or {}
    text       = data.get('text', '').strip()

    if not text:
        return jsonify({'message': 'Message text is required.'}), 400

    msg = Message(conversation_id=conv_id, sender_id=student_id, text=text)
    db.session.add(msg)
    db.session.commit()
    return jsonify(msg.to_dict(student_id)), 201
