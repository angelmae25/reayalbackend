# =============================================================================
# FILE PATH: app/routes/org_posts.py
#
# FIXES vs previous version:
#   1. /organizations/<org_id> now accepts BOTH plain integers ("2") AND
#      "org_"-prefixed strings ("org_2") — strips the prefix server-side.
#   2. /my-organizations now requires JWT (token must be sent from Flutter).
#   3. _resolve_db_id() unchanged — still handles all ID formats.
# =============================================================================

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import text
from .. import db

org_posts_bp = Blueprint('org_posts', __name__)


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: resolve any student identifier → integer DB primary key
# ─────────────────────────────────────────────────────────────────────────────
def _resolve_db_id(student_id_param: str, user_id_param: str):
    """
    Returns the integer PK of the student, or None if not found.
    Priority:
      1. userId param (numeric DB PK)
      2. studentId param if numeric (also a DB PK)
      3. studentId as a student-number string → look up in students table
    """
    # 1. userId is usually the numeric DB PK
    if user_id_param and user_id_param.strip().isdigit():
        return int(user_id_param.strip())

    # 2. studentId that happens to be numeric
    if student_id_param and student_id_param.strip().isdigit():
        return int(student_id_param.strip())

    # 3. studentId as string student number (e.g. "S1001", "2021-00123")
    if student_id_param and student_id_param.strip():
        row = db.session.execute(
            text("SELECT id FROM students WHERE student_id = :sid LIMIT 1"),
            {'sid': student_id_param.strip()}
        ).fetchone()
        if row:
            return int(row[0])

    return None


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: strip "org_" prefix and convert to int
# ─────────────────────────────────────────────────────────────────────────────
def _parse_org_id(raw: str):
    """
    Accepts '2', 'org_2', '10', 'org_10', etc.
    Returns an integer, or None if it cannot be parsed.
    """
    raw = str(raw).strip()
    if raw.startswith('org_'):
        raw = raw[4:]          # strip "org_" prefix
    try:
        return int(raw)
    except (ValueError, TypeError):
        return None


# ─────────────────────────────────────────────────────────────────────────────
# GET /my-organizations
# Returns organizations where the student has an officer role.
# Accepts ?studentId=<value> and/or ?userId=<value>
# Falls back to JWT identity when no query params are supplied.
# ─────────────────────────────────────────────────────────────────────────────
@org_posts_bp.route('/my-organizations', methods=['GET'])
@jwt_required()
def my_organizations():
    student_id_param = request.args.get('studentId', '').strip()
    user_id_param    = request.args.get('userId',    '').strip()

    # Fall back to JWT identity when no params supplied
    if not student_id_param and not user_id_param:
        jwt_identity  = get_jwt_identity()
        user_id_param = str(jwt_identity) if jwt_identity else ''

    sid = _resolve_db_id(student_id_param, user_id_param)

    if not sid:
        return jsonify([]), 200

    rows = db.session.execute(text("""
                                   SELECT oa.id                     AS assignment_id,
                                          o.id                      AS organization_id,
                                          o.name                    AS organization_name,
                                          COALESCE(o.acronym, '')   AS acronym,
                                          COALESCE(r.role_name, '') AS role_name
                                   FROM role_assignments oa
                                            JOIN organizations o ON o.id = oa.organization_id
                                            JOIN roles r ON r.id = oa.role_id
                                   WHERE oa.student_id = :sid
                                     AND o.status = 'ACTIVE'
                                   ORDER BY o.name ASC
                                   """), {'sid': sid}).fetchall()

    result = [
        {
            'assignmentId':     row.assignment_id,
            'organizationId':   row.organization_id,
            'organizationName': row.organization_name,
            'acronym':          row.acronym,
            'roleName':         row.role_name,
        }
        for row in rows
    ]

    return jsonify(result), 200


# ─────────────────────────────────────────────────────────────────────────────
# POST /news  — officer posts a news article
# ─────────────────────────────────────────────────────────────────────────────
@org_posts_bp.route('/news/', methods=['POST'])
@jwt_required()
def post_news():
    data            = request.get_json(force=True) or {}
    student_id      = data.get('studentId')
    organization_id = data.get('organizationId')
    title           = data.get('title', '').strip()
    body            = data.get('body', '').strip()
    category        = data.get('category', 'campus').strip()
    is_featured     = bool(data.get('isFeatured', False))

    if not all([student_id, organization_id, title, body]):
        return jsonify({'message': 'studentId, organizationId, title and body are required'}), 400

    if not _is_officer(student_id, organization_id):
        return jsonify({'message': 'No officer role found for this student in this organization.'}), 403

    db.session.execute(text("""
        INSERT INTO news (student_id, organization_id, title, body, category, is_featured, published_at)
        VALUES (:sid, :oid, :title, :body, :category, :featured, NOW())
    """), {
        'sid':      student_id,
        'oid':      organization_id,
        'title':    title,
        'body':     body,
        'category': category,
        'featured': 1 if is_featured else 0,
    })
    db.session.commit()

    return jsonify({'message': 'News posted successfully.'}), 201


# ─────────────────────────────────────────────────────────────────────────────
# POST /events  — officer posts an event
# ─────────────────────────────────────────────────────────────────────────────
@org_posts_bp.route('/events/', methods=['POST'])
@jwt_required()
def post_event():
    data            = request.get_json(force=True) or {}
    student_id      = data.get('studentId')
    organization_id = data.get('organizationId')
    short_name      = data.get('shortName', '').strip()
    full_name       = data.get('fullName', '').strip()
    date            = data.get('date', '').strip()
    venue           = data.get('venue', '').strip()
    category        = data.get('category', 'General').strip()
    description     = data.get('description', '').strip()
    color           = data.get('color', '#8B1A1A').strip()

    if not all([student_id, organization_id, short_name, full_name, date, venue]):
        return jsonify({'message': 'Missing required fields.'}), 400

    if not _is_officer(student_id, organization_id):
        return jsonify({'message': 'No officer role found for this student in this organization.'}), 403

    db.session.execute(text("""
        INSERT INTO events
            (student_id, organization_id, short_name, full_name, date, venue, category, description, color)
        VALUES
            (:sid, :oid, :sname, :fname, :date, :venue, :cat, :desc, :color)
    """), {
        'sid':   student_id,
        'oid':   organization_id,
        'sname': short_name,
        'fname': full_name,
        'date':  date,
        'venue': venue,
        'cat':   category,
        'desc':  description,
        'color': color,
    })
    db.session.commit()

    return jsonify({'message': 'Event posted successfully.'}), 201


# ─────────────────────────────────────────────────────────────────────────────
# GET /organizations/<org_id>  — org detail + officers (for Clubs view)
#
# FIX: accepts both plain integers ("2") and "org_"-prefixed strings ("org_2").
#      The route uses string type so Flask doesn't reject "org_2" before
#      we even get to parse it.
# ─────────────────────────────────────────────────────────────────────────────
@org_posts_bp.route('/organizations/<org_id>', methods=['GET'])
def get_org_detail(org_id):
    # Resolve the org ID regardless of whether Flutter sent "2" or "org_2"
    parsed_id = _parse_org_id(org_id)
    if parsed_id is None:
        return jsonify({'message': f'Invalid organization ID: {org_id}'}), 400

    org = db.session.execute(text("""
        SELECT id, name, acronym, status, adviser, year_founded, description
        FROM organizations
        WHERE id = :oid
    """), {'oid': parsed_id}).fetchone()

    if not org:
        return jsonify({'message': 'Organization not found.'}), 404

    officers = db.session.execute(text("""
                                       SELECT CONCAT(s.first_name, ' ', s.last_name) AS name,
                                              s.student_id                           AS studentId,
                                              s.course,
                                              COALESCE(r.role_name, '')              AS role
                                       FROM role_assignments ra
                                                JOIN students s ON s.id = ra.student_id
                                                JOIN roles r ON r.id = ra.role_id
                                       WHERE ra.organization_id = :oid
                                       ORDER BY r.role_name ASC
                                       """), {'oid': parsed_id}).fetchall()

    return jsonify({
        'id':          org.id,
        'name':        org.name,
        'acronym':     org.acronym or '',
        'adviser':     org.adviser or '',
        'yearFounded': org.year_founded,
        'description': org.description or '',
        'officers': [
            {
                'name':      o.name,
                'studentId': o.studentId,
                'course':    o.course or '',
                'role':      o.role   or '',
            }
            for o in officers
        ]
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
# INTERNAL: check if a student is an officer of an org
# ─────────────────────────────────────────────────────────────────────────────
def _is_officer(student_id, organization_id) -> bool:
    sid = _resolve_db_id('', str(student_id))
    if not sid:
        sid = _resolve_db_id(str(student_id), '')
    if not sid:
        return False

    row = db.session.execute(text("""
        SELECT id FROM role_assignments
        WHERE student_id = :sid AND organization_id = :oid
        LIMIT 1
    """), {'sid': sid, 'oid': organization_id}).fetchone()

    return row is not None