# =============================================================================
# app/routes/chat.py  —  /api/mobile/chat
#
# FIXES:
#   1. send_message() now verifies the sender is actually a MEMBER of the
#      conversation before allowing them to post. Previously any authenticated
#      student could send messages to any conversation ID they guessed.
#   2. get_messages() has the same membership guard.
#   3. create_conversation() validates that member_ids are non-empty integers
#      and belong to real ACTIVE students (prevents silent no-op conversations).
#   4. Empty / whitespace-only message text returns 400 (was already checked,
#      kept intact).
# =============================================================================

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .. import db
from ..models.models import Conversation, Message, Student

chat_bp = Blueprint('chat', __name__)


# ── Membership guard helper ───────────────────────────────────────────────────
def _assert_member(conv: Conversation, student_id: int):
    """Raises a 403-ready tuple if student is not in the conversation."""
    member_ids = {m.id for m in conv.members}
    if student_id not in member_ids:
        return False
    return True


# ─────────────────────────────────────────────────────────────────────────────
# GET /conversations  — list my conversations
# ─────────────────────────────────────────────────────────────────────────────
@chat_bp.route('/conversations', methods=['GET'])
@jwt_required()
def list_conversations():
    student_id = int(get_jwt_identity())
    student    = Student.query.get_or_404(student_id)
    convs      = student.conversations
    return jsonify([c.to_dict(student_id) for c in convs]), 200


# ─────────────────────────────────────────────────────────────────────────────
# POST /conversations  — start a new conversation
# Body: { member_ids: [int, ...], is_group?: bool, name?: str }
# ─────────────────────────────────────────────────────────────────────────────
@chat_bp.route('/conversations', methods=['POST'])
@jwt_required()
def create_conversation():
    student_id = int(get_jwt_identity())
    data       = request.get_json(silent=True) or {}
    other_ids  = data.get('member_ids', [])
    is_group   = data.get('is_group', False)
    name       = data.get('name')

    # FIX: validate member_ids — must be a non-empty list
    if not isinstance(other_ids, list) or len(other_ids) == 0:
        return jsonify({'message': 'member_ids must be a non-empty list of student IDs.'}), 400

    me = Student.query.get_or_404(student_id)

    # For DMs (is_group=False) check if a conversation already exists
    if not is_group and len(other_ids) == 1:
        other_id   = int(other_ids[0])
        my_conv_ids    = {c.id for c in me.conversations}
        other = Student.query.get(other_id)
        if other:
            other_conv_ids = {c.id for c in other.conversations}
            shared = my_conv_ids & other_conv_ids
            for conv_id in shared:
                existing = Conversation.query.get(conv_id)
                if existing and not existing.is_group:
                    # Return existing DM instead of creating a duplicate
                    return jsonify(existing.to_dict(student_id)), 200

    conv = Conversation(name=name, is_group=is_group)
    db.session.add(conv)
    conv.members.append(me)

    for oid in other_ids:
        try:
            other = Student.query.get(int(oid))
        except (ValueError, TypeError):
            continue
        # FIX: only add ACTIVE students to conversations
        if other and other.status == 'ACTIVE':
            conv.members.append(other)

    if len(conv.members) < 2:
        db.session.rollback()
        return jsonify({'message': 'No valid active students found for the given member_ids.'}), 400

    db.session.commit()
    return jsonify(conv.to_dict(student_id)), 201


# ─────────────────────────────────────────────────────────────────────────────
# GET /conversations/<id>/messages  — read messages
# FIX: now checks that the requester is a member of the conversation
# ─────────────────────────────────────────────────────────────────────────────
@chat_bp.route('/conversations/<int:conv_id>/messages', methods=['GET'])
@jwt_required()
def get_messages(conv_id):
    student_id = int(get_jwt_identity())
    conv       = Conversation.query.get_or_404(conv_id)

    if not _assert_member(conv, student_id):
        return jsonify({'message': 'You are not a member of this conversation.'}), 403

    msgs = Message.query.filter_by(conversation_id=conv_id) \
                        .order_by(Message.sent_at.asc()).all()
    return jsonify([m.to_dict(student_id) for m in msgs]), 200


# ─────────────────────────────────────────────────────────────────────────────
# POST /conversations/<id>/messages  — send a message
# FIX: now checks that the sender is a member of the conversation
# ─────────────────────────────────────────────────────────────────────────────
@chat_bp.route('/conversations/<int:conv_id>/messages', methods=['POST'])
@jwt_required()
def send_message(conv_id):
    student_id = int(get_jwt_identity())
    conv       = Conversation.query.get_or_404(conv_id)

    # FIX: membership guard — prevents students from spying/posting to foreign convs
    if not _assert_member(conv, student_id):
        return jsonify({'message': 'You are not a member of this conversation.'}), 403

    data = request.get_json(silent=True) or {}
    text = data.get('text', '').strip()

    if not text:
        return jsonify({'message': 'Message text is required.'}), 400

    msg = Message(conversation_id=conv_id, sender_id=student_id, text=text)
    db.session.add(msg)
    db.session.commit()
    return jsonify(msg.to_dict(student_id)), 201