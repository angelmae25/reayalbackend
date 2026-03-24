# =============================================================================
# app/routes/reports.py  —  /api/mobile/reports
# POST /   — student submits a problem report
# GET  /   — student views their own reports
# =============================================================================

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import text
from .. import db

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/', methods=['POST'])
@jwt_required()
def submit_report():
    """
    Student submits a report from the mobile app Settings → Report a Problem.
    Writes directly to the reports table which Spring Boot admin dashboard reads.
    """
    student_id = int(get_jwt_identity())
    data       = request.get_json(silent=True) or {}
    subject    = data.get('subject', '').strip()
    message    = data.get('message', '').strip()

    if not subject:
        return jsonify({'message': 'Subject is required.'}), 400
    if not message:
        return jsonify({'message': 'Message is required.'}), 400
    if len(subject) > 200:
        return jsonify({'message': 'Subject must be under 200 characters.'}), 400

    try:
        db.session.execute(text(
            "INSERT INTO reports (student_id, subject, message, status, created_at) "
            "VALUES (:sid, :sub, :msg, 'OPEN', NOW())"
        ), {
            'sid': student_id,
            'sub': subject,
            'msg': message,
        })
        db.session.commit()
        return jsonify({'message': 'Report submitted successfully.'}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Failed to submit report: {str(e)}'}), 500


@reports_bp.route('/', methods=['GET'])
@jwt_required()
def get_my_reports():
    """
    Returns all reports submitted by the current student.
    Useful for showing students their report history in the app.
    """
    student_id = int(get_jwt_identity())

    try:
        result = db.session.execute(text(
            "SELECT id, subject, message, status, admin_reply, "
            "replied_at, created_at "
            "FROM reports "
            "WHERE student_id = :sid "
            "ORDER BY created_at DESC"
        ), {'sid': student_id})

        rows    = result.mappings().all()
        reports = []
        for r in rows:
            reports.append({
                'id':          r['id'],
                'subject':     r['subject'],
                'message':     r['message'],
                'status':      r['status'],
                'admin_reply': r['admin_reply'],
                'replied_at':  r['replied_at'].isoformat() if r['replied_at'] else None,
                'created_at':  r['created_at'].isoformat() if r['created_at'] else None,
            })
        return jsonify(reports), 200

    except Exception as e:
        return jsonify({'message': f'Failed to load reports: {str(e)}'}), 500