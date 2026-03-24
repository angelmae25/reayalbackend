# =============================================================================
# app/routes/auth.py
# =============================================================================

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity,
)
from .. import db, bcrypt
from ..models.models import Student

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or {}
    required = ['full_name', 'student_id', 'email', 'password']
    for field in required:
        if not data.get(field):
            return jsonify({'message': f'{field} is required.'}), 400

    parts      = data['full_name'].strip().split(' ', 1)
    first_name = parts[0]
    last_name  = parts[1] if len(parts) > 1 else ''

    if Student.query.filter_by(email=data['email'].lower()).first():
        return jsonify({'message': 'Email already registered.'}), 409
    if Student.query.filter_by(student_id=data['student_id']).first():
        return jsonify({'message': 'Student ID already registered.'}), 409

    pw_hash = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    student = Student(
        student_id    = data['student_id'],
        first_name    = first_name,
        last_name     = last_name,
        email         = data['email'].lower(),
        password_hash = pw_hash,
        course        = data.get('course', ''),
        year_level    = data.get('year_level', '1st Year'),
        status        = 'ACTIVE',
    )
    db.session.add(student)
    db.session.commit()

    access_token  = create_access_token(identity=str(student.id))
    refresh_token = create_refresh_token(identity=str(student.id))
    return jsonify({
        'message':       'Account created successfully!',
        'access_token':  access_token,
        'refresh_token': refresh_token,
        'student':       student.to_dict(),
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data     = request.get_json(silent=True) or {}
    email    = data.get('email', '').lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'message': 'Email and password are required.'}), 400

    student = Student.query.filter_by(email=email).first()
    if not student or not bcrypt.check_password_hash(student.password_hash, password):
        return jsonify({'message': 'Invalid email or password.'}), 401
    if student.status == 'INACTIVE':
        return jsonify({'message': 'Account deactivated. Contact your admin.'}), 403

    access_token  = create_access_token(identity=str(student.id))
    refresh_token = create_refresh_token(identity=str(student.id))
    return jsonify({
        'access_token':  access_token,
        'refresh_token': refresh_token,
        'student':       student.to_dict(),
    }), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    student_id = int(get_jwt_identity())
    student    = Student.query.get_or_404(student_id)
    return jsonify(student.to_dict()), 200


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    identity     = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify({'access_token': access_token}), 200


# ─────────────────────────────────────────────────────────────────────────────
# CHANGE PASSWORD  ← NEW
# PUT /api/mobile/auth/change-password
# Body: { "current_password": "...", "new_password": "..." }
# ─────────────────────────────────────────────────────────────────────────────
@auth_bp.route('/change-password', methods=['PUT'])
@jwt_required()
def change_password():
    student_id = int(get_jwt_identity())
    student    = Student.query.get_or_404(student_id)
    data       = request.get_json(silent=True) or {}

    current_pw = data.get('current_password', '').strip()
    new_pw     = data.get('new_password', '').strip()

    if not current_pw or not new_pw:
        return jsonify({'message': 'Both current and new password are required.'}), 400

    if not bcrypt.check_password_hash(student.password_hash, current_pw):
        return jsonify({'message': 'Current password is incorrect.'}), 401

    if len(new_pw) < 6:
        return jsonify({'message': 'New password must be at least 6 characters.'}), 400

    student.password_hash = bcrypt.generate_password_hash(new_pw).decode('utf-8')
    db.session.commit()

    return jsonify({'message': 'Password updated successfully.'}), 200


# ─────────────────────────────────────────────────────────────────────────────
# SAVE FCM TOKEN  ← NEW
# POST /api/mobile/auth/fcm-token
# Body: { "fcm_token": "..." }
# Called by Flutter on app start after Firebase initializes.
# Saves the device token so Flask can send push notifications.
# ─────────────────────────────────────────────────────────────────────────────
@auth_bp.route('/fcm-token', methods=['POST'])
@jwt_required()
def save_fcm_token():
    student_id = int(get_jwt_identity())
    student    = Student.query.get_or_404(student_id)
    data       = request.get_json(silent=True) or {}

    token = data.get('fcm_token', '').strip()
    if not token:
        return jsonify({'message': 'fcm_token is required.'}), 400

    student.fcm_token = token
    db.session.commit()

    return jsonify({'message': 'FCM token saved.'}), 200


@auth_bp.route('/admin/students', methods=['GET'])
@jwt_required()
def admin_students():
    status = request.args.get('status', 'all')
    query  = Student.query.order_by(Student.created_at.desc())
    if status == 'active':
        query = query.filter_by(status='ACTIVE')
    elif status == 'inactive':
        query = query.filter_by(status='INACTIVE')
    students = query.all()
    return jsonify([{
        'id':         s.id,
        'student_id': s.student_id,
        'full_name':  s.full_name,
        'email':      s.email,
        'course':     s.course,
        'year_level': s.year_level,
        'status':     s.status,
        'points':     s.points,
        'created_at': s.created_at.isoformat(),
    } for s in students]), 200


@auth_bp.route('/admin/students/<int:student_id>/status', methods=['PUT'])
@jwt_required()
def update_student_status(student_id):
    student    = Student.query.get_or_404(student_id)
    data       = request.get_json(silent=True) or {}
    new_status = data.get('status', '').upper()
    if new_status not in ('ACTIVE', 'INACTIVE'):
        return jsonify({'message': 'Status must be ACTIVE or INACTIVE.'}), 400
    student.status = new_status
    db.session.commit()
    return jsonify({
        'message': f'Student {student.full_name} is now {new_status}.',
        'student': student.to_dict(),
    }), 200