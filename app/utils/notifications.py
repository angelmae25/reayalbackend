# =============================================================================
# app/utils/notifications.py
# Push notification helper using Firebase Cloud Messaging (FCM).
#
# To enable real push notifications:
#   1. Go to Firebase Console > Project Settings > Service Accounts
#   2. Click "Generate new private key" — save the JSON file
#   3. pip install firebase-admin
#   4. Set FIREBASE_CREDENTIALS_PATH env var to the JSON file path
#      e.g. FIREBASE_CREDENTIALS_PATH=/path/to/serviceAccountKey.json
#
# Without setup, all push calls are silently skipped (no crash).
# =============================================================================

import os

_firebase_initialized = False


def _init_firebase():
    global _firebase_initialized
    if _firebase_initialized:
        return True
    creds_path = os.environ.get('FIREBASE_CREDENTIALS_PATH', '')
    if not creds_path or not os.path.exists(creds_path):
        return False
    try:
        import firebase_admin
        from firebase_admin import credentials
        cred = credentials.Certificate(creds_path)
        firebase_admin.initialize_app(cred)
        _firebase_initialized = True
        return True
    except Exception as e:
        print(f'[FCM] Firebase init failed: {e}')
        return False


def send_push_to_all(title: str, body: str, data: dict = None):
    """
    Send a push notification to every student who has an FCM token.
    Silently skipped if Firebase is not configured.
    """
    if not _init_firebase():
        print('[FCM] Firebase not configured — push notification skipped.')
        return

    try:
        from firebase_admin import messaging
        from app import db
        from app.models.models import Student

        tokens = [
            s.fcm_token for s in
            Student.query.filter(Student.fcm_token.isnot(None)).all()
        ]
        if not tokens:
            return

        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=body),
            data={k: str(v) for k, v in (data or {}).items()},
            tokens=tokens,
        )
        response = messaging.send_each_for_multicast(message)
        print(f'[FCM] Sent {response.success_count}/{len(tokens)} notifications.')
    except Exception as e:
        print(f'[FCM] Push send failed: {e}')


def send_push_to_student(student_fcm_token: str, title: str, body: str, data: dict = None):
    """
    Send a push notification to a single student by their FCM token.
    Silently skipped if Firebase is not configured.
    """
    if not student_fcm_token:
        return
    if not _init_firebase():
        return

    try:
        from firebase_admin import messaging
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data={k: str(v) for k, v in (data or {}).items()},
            token=student_fcm_token,
        )
        messaging.send(message)
    except Exception as e:
        print(f'[FCM] Push to student failed: {e}')