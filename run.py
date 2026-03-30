# =============================================================================
# run.py  —  Entry point for PyCharm
#
# HOW TO RUN IN PYCHARM:
#   1. Open this project folder in PyCharm
#   2. Create a virtual environment:  File > Settings > Python Interpreter > Add
#   3. Install requirements:  pip install -r requirements.txt
#   4. Set environment variable DB_PASS to your MySQL root password
#      (Run > Edit Configurations > Environment Variables)
#   5. Run this file — Flask starts on http://localhost:5000
#
# Android Emulator connects via:  http://10.0.2.2:5000/api/mobile/...
# Physical device connects via:   http://<YOUR_PC_LAN_IP>:5000/api/mobile/...
# =============================================================================

from app import create_app, db, socketio

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("✅  Database tables ready.")

    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)