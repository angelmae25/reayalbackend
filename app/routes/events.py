# =============================================================================
# app/routes/events.py  —  /api/mobile/events
#
# FIXES:
#   1. POST / now enforces role assignment — only org officers can post
#   2. POST / now saves organization_id (was missing, breaking the FK)
#   3. GET /  now returns is_attending flag per student (avoids extra round-trip)
#   4. Push notification on create is preserved
# =============================================================================

from datetime import date
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .. import db
from ..models.models import Event, Student, EventAttendance, RoleAssignment

events_bp = Blueprint('events', __name__)


def _resolve_org(student, requested_org_id):
    assignments = RoleAssignment.query.filter_by(student_id=student.id).all()
    if not assignments:
        raise ValueError('You do not have a role in any organization and cannot post events.')
    org_ids = {a.organization_id for a in assignments}
    if requested_org_id is not None:
        if int(requested_org_id) not in org_ids:
            raise ValueError('You are not an officer of the requested organization.')
        return int(requested_org_id)
    return assignments[0].organization_id


@events_bp.route('/', methods=['GET'])
@jwt_required()
def list_events():
    student_id = int(get_jwt_identity())
    events = Event.query.order_by(Event.date.asc()).all()
    result = []
    for e in events:
        d = e.to_dict()
        d['is_attending'] = EventAttendance.query.filter_by(
            event_id=e.id, student_id=student_id).first() is not None
        result.append(d)
    return jsonify(result), 200


@events_bp.route('/<int:event_id>', methods=['GET'])
@jwt_required()
def get_event(event_id):
    student_id = int(get_jwt_identity())
    event = Event.query.get_or_404(event_id)
    d = event.to_dict()
    d['is_attending'] = EventAttendance.query.filter_by(
        event_id=event_id, student_id=student_id).first() is not None
    return jsonify(d), 200


@events_bp.route('/', methods=['POST'])
@jwt_required()
def create_event():
    student_id = int(get_jwt_identity())
    student    = Student.query.get_or_404(student_id)
    data       = request.get_json(silent=True) or {}

    for field in ['short_name', 'full_name', 'date', 'venue']:
        if not data.get(field, '').strip():
            return jsonify({'message': f'{field} is required.'}), 400

    try:
        org_id = _resolve_org(student, data.get('organization_id'))
    except ValueError as e:
        return jsonify({'message': str(e)}), 403

    try:
        event_date = date.fromisoformat(data['date'])
    except (ValueError, KeyError):
        return jsonify({'message': 'date must be in YYYY-MM-DD format.'}), 400

    event = Event(
        short_name      = data['short_name'].strip().upper(),
        full_name       = data['full_name'].strip(),
        date            = event_date,
        venue           = data['venue'].strip(),
        category        = data.get('category', 'General'),
        color           = data.get('color', '#8B1A1A'),
        description     = data.get('description', ''),
        organization_id = org_id,
    )
    db.session.add(event)
    db.session.commit()

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


@events_bp.route('/<int:event_id>/attend', methods=['POST'])
@jwt_required()
def attend_event(event_id):
    student_id = int(get_jwt_identity())
    event   = Event.query.get_or_404(event_id)
    student = Student.query.get_or_404(student_id)
    existing = EventAttendance.query.filter_by(event_id=event_id, student_id=student_id).first()
    if existing:
        return jsonify({'message': 'Already marked attendance.', 'points': student.points, 'already_attended': True}), 200
    POINTS_PER_EVENT = 10
    db.session.add(EventAttendance(event_id=event_id, student_id=student_id))
    student.points = (student.points or 0) + POINTS_PER_EVENT
    db.session.commit()
    return jsonify({'message': f'Attendance marked! You earned {POINTS_PER_EVENT} points.',
                    'points': student.points, 'event_name': event.full_name, 'already_attended': False}), 201


# Change /attendance to /attended
@events_bp.route('/<int:event_id>/attended', methods=['GET'])
@jwt_required()
def check_attendance(event_id):
    student_id = int(get_jwt_identity())
    attended = EventAttendance.query.filter_by(
        event_id=event_id, student_id=student_id
    ).first() is not None
    return jsonify({'attended': attended}), 200


@events_bp.route('/<int:event_id>/attendees', methods=['GET'])
@jwt_required()
def get_attendees(event_id):
    Event.query.get_or_404(event_id)
    attendances = EventAttendance.query.filter_by(event_id=event_id).all()
    result = []
    for a in attendances:
        s = Student.query.get(a.student_id)
        if s:
            result.append({'student_id': s.student_id, 'full_name': s.full_name,
                           'course': s.course, 'year_level': s.year_level,
                           'attended_at': a.attended_at.isoformat()})
    return jsonify(result), 200