# =============================================================================
# FILE PATH: app/routes/chat_socket.py  — FIXED VERSION
# Fix: broadcast message without is_mine so each client determines it locally.
# Fix: include conversation_id in broadcast so ChatController can route it.
# =============================================================================

from flask_jwt_extended import decode_token
from .. import db
from ..models.models import Message, Conversation, Student


def register_socket_events(socketio):

    @socketio.on('connect')
    def on_connect(auth):
        try:
            token      = auth.get('token', '') if auth else ''
            decoded    = decode_token(token)
            student_id = int(decoded['sub'])
            print(f'[Socket] ✅ Student {student_id} connected')
        except Exception as e:
            print(f'[Socket] ❌ Auth failed: {e}')
            return False

    @socketio.on('disconnect')
    def on_disconnect():
        print('[Socket] Client disconnected')

    @socketio.on('join_conversation')
    def on_join(data):
        from flask_socketio import join_room, emit
        conv_id = str(data.get('conversation_id', ''))
        if conv_id:
            join_room(conv_id)
            emit('joined', {'conversation_id': conv_id}, room=conv_id)

    @socketio.on('leave_conversation')
    def on_leave(data):
        from flask_socketio import leave_room
        conv_id = str(data.get('conversation_id', ''))
        if conv_id:
            leave_room(conv_id)

    @socketio.on('send_message')
    def on_message(data):
        from flask_socketio import emit
        try:
            token      = data.get('token', '')
            decoded    = decode_token(token)
            student_id = int(decoded['sub'])
            conv_id    = int(data.get('conversation_id'))
            text       = data.get('text', '').strip()

            if not text:
                return

            # Save to database
            msg = Message(
                conversation_id=conv_id,
                sender_id=student_id,
                text=text,
            )
            db.session.add(msg)
            db.session.commit()

            student = Student.query.get(student_id)

            # ── FIX: broadcast WITHOUT is_mine ─────────────────────────────
            # Each Flutter client checks if sender_id == their own id
            # to determine is_mine locally. This is the correct approach.
            payload = {
                'id':              str(msg.id),
                'text':            msg.text,
                'sender_id':       str(student_id),
                'sender_name':     student.full_name if student else '',
                'sent_at':         msg.sent_at.isoformat(),
                'conversation_id': str(conv_id),  # ← ADDED so Flutter can route
                # NO is_mine here — client decides based on sender_id
            }
            emit('new_message', payload, room=str(conv_id))

        except Exception as e:
            from flask_socketio import emit as _emit
            _emit('error', {'message': str(e)})

    @socketio.on('start_dm')
    def on_start_dm(data):
        from flask_socketio import emit
        try:
            token    = data.get('token', '')
            decoded  = decode_token(token)
            my_id    = int(decoded['sub'])
            other_id = int(data.get('other_student_id'))

            me    = Student.query.get(my_id)
            other = Student.query.get(other_id)

            if not me or not other:
                emit('error', {'message': 'Student not found.'})
                return

            if my_id == other_id:
                emit('error', {'message': 'Cannot start a conversation with yourself.'})
                return

            # Find existing 1-on-1 conversation
            existing = None
            for conv in me.conversations:
                if not conv.is_group and other in conv.members:
                    existing = conv
                    break

            if not existing:
                existing = Conversation(
                    name=f'{me.full_name} & {other.full_name}',
                    is_group=False,
                )
                existing.members.append(me)
                existing.members.append(other)
                db.session.add(existing)
                db.session.commit()

            emit('dm_ready', {'conversation_id': str(existing.id)})

        except Exception as e:
            from flask_socketio import emit as _emit
            _emit('error', {'message': str(e)})