# =============================================================================
# app/routes/events.py  —  /api/mobile/events
# =============================================================================

from datetime import date
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .. import db
from ..models.models import Event, Student, EventAttendance

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

    # ── Send push notification to all students when event is posted ──────────
    try:
        from ..utils.notifications import send_push_to_all
        send_push_to_all(
            title=f'New Event: {event.short_name}',
            body=f'{event.full_name} at {event.venue}',
            data={'type': 'event', 'event_id': str(event.id)},
        )
    except Exception as e:
        print(f'[FCM] Push notification skipped: {e}')

    return jsonify(event.to_dict()), 201


# ─────────────────────────────────────────────────────────────────────────────
# ATTEND EVENT  ← NEW
# POST /api/mobile/events/<id>/attend
# Marks a student as attending and awards +10 points.
# Duplicate attendance is silently ignored (returns current points).
# ─────────────────────────────────────────────────────────────────────────────
@events_bp.route('/<int:event_id>/attend', methods=['POST'])
@jwt_required()
def attend_event(event_id):
    student_id = int(get_jwt_identity())
    event      = Event.query.get_or_404(event_id)
    student    = Student.query.get_or_404(student_id)

    # Check if student already attended — prevent duplicate points
    already = EventAttendance.query.filter_by(
        event_id=event_id,
        student_id=student_id,
    ).first()

    if already:
        return jsonify({
            'message': 'You have already marked attendance for this event.',
            'points':  student.points,
            'already_attended': True,
        }), 200

    # Award points and record attendance
    POINTS_PER_EVENT = 10
    attendance = EventAttendance(
        event_id=event_id,
        student_id=student_id,
    )
    student.points = (student.points or 0) + POINTS_PER_EVENT
    db.session.add(attendance)
    db.session.commit()

    return jsonify({
        'message':          f'Attendance marked! You earned {POINTS_PER_EVENT} points.',
        'points':           student.points,
        'event_name':       event.full_name,
        'already_attended': False,
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
# CHECK ATTENDANCE  ← NEW
# GET /api/mobile/events/<id>/attendance
# Returns whether the current student has already attended this event.
# Used by Flutter to show Attend vs Attended button state on app load.
# ─────────────────────────────────────────────────────────────────────────────
@events_bp.route('/<int:event_id>/attendance', methods=['GET'])
@jwt_required()
def check_attendance(event_id):
    student_id = int(get_jwt_identity())

    attended = EventAttendance.query.filter_by(
        event_id=event_id,
        student_id=student_id,
    ).first() is not None

    return jsonify({'attended': attended}), 200


# ─────────────────────────────────────────────────────────────────────────────
# EVENT ATTENDEES  ← NEW
# GET /api/mobile/events/<id>/attendees
# Returns list of students who attended (useful for admin/officer views).
# ─────────────────────────────────────────────────────────────────────────────
@events_bp.route('/<int:event_id>/attendees', methods=['GET'])
@jwt_required()
def get_attendees(event_id):
    Event.query.get_or_404(event_id)  # 404 if event not found

    attendances = EventAttendance.query.filter_by(event_id=event_id).all()
    result = []
    for a in attendances:
        s = Student.query.get(a.student_id)
        if s:
            result.append({
                'student_id':  s.student_id,
                'full_name':   s.full_name,
                'course':      s.course,
                'year_level':  s.year_level,
                'attended_at': a.attended_at.isoformat(),
            })

    return jsonify(result), 200