# Scholife Flask Backend — Setup Guide
# ======================================
# Complete step-by-step instructions for PyCharm + MySQL + Android

## PROJECT STRUCTURE
```
scholife_backend/
├── run.py                      ← PyCharm entry point (run this)
├── requirements.txt            ← pip dependencies
├── Schoolifetrue_db.sql             ← MySQL database schema + seed data
├── flutter_auth_service.dart   ← REPLACE lib/services/auth_service.dart
├── flutter_data_service.dart   ← REPLACE lib/services/data_service.dart
├── flutter_pubspec.yaml        ← REPLACE pubspec.yaml (adds sqflite + path)
└── app/
    ├── __init__.py             ← Flask factory + extensions
    ├── config.py               ← DB credentials, JWT secret
    ├── models/
    │   └── models.py           ← SQLAlchemy ORM models
    └── routes/
        ├── auth.py             ← POST /register  POST /login  GET /me
        ├── news.py             ← GET/POST /news/
        ├── events.py           ← GET/POST /events/
        ├── clubs.py            ← GET /clubs/  POST /clubs/<id>/join|leave
        ├── marketplace.py      ← CRUD /marketplace/
        ├── lost_found.py       ← CRUD /lost-found/
        ├── chat.py             ← GET/POST conversations + messages
        ├── leaderboard.py      ← GET /leaderboard/
        └── students.py         ← GET/PUT /students/profile
```

---

## STEP 1 — SET UP MYSQL DATABASE

### Option A: MySQL Workbench
1. Open MySQL Workbench and connect to localhost
2. Click File > Open SQL Script > select `Schoolifetrue_db.sql`
3. Click the lightning bolt (Execute All) button
4. You should see `Schoolifetrue_db` appear in the schema list

### Option B: Command line
```bash
mysql -u root -p < Schoolifetrue_db.sql
```

### Option C: PyCharm Database tool
1. View > Tool Windows > Database
2. Click + > Data Source > MySQL
3. Host: localhost  Port: 3306  User: root  Password: (yours)
4. Open a console, paste the contents of Schoolifetrue_db.sql, run it

### Verify seed data was inserted:
```sql
USE Schoolifetrue_db;
SELECT * FROM students;     -- should show 3 rows
SELECT * FROM news;         -- should show 5 rows
SELECT * FROM events;       -- should show 4 rows
SELECT * FROM clubs;        -- should show 6 rows
```

---

## STEP 2 — SET UP FLASK IN PYCHARM

### 2a. Open the project
- Open PyCharm > Open > select the `scholife_backend/` folder

### 2b. Create a virtual environment
- File > Settings > Project > Python Interpreter
- Click the gear icon > Add Interpreter > Add Local Interpreter
- Select "Virtualenv Environment" > OK
- PyCharm will create a `.venv` folder

### 2c. Install dependencies
Open the PyCharm Terminal (bottom bar) and run:
```bash
pip install -r requirements.txt
```

### 2d. Set your MySQL password
- Run > Edit Configurations > + > Python
- Script: `run.py`
- Environment variables: click the icon and add:
  ```
  DB_PASS=your_mysql_password_here
  DB_USER=root
  DB_NAME=Schoolifetrue_db
  ```
  (If your password is empty, set DB_PASS to an empty string)

### 2e. Run the server
- Click the green Run button (or Shift+F10)
- You should see:
  ```
  ✅  Database tables ready.
  * Running on http://0.0.0.0:5000
  ```

### 2f. Test it in a browser or Postman
- http://localhost:5000/api/mobile/ping  → should return `{"status":"ok"}`

---

## STEP 3 — UPDATE FLUTTER FILES

### 3a. Replace auth_service.dart
Copy `flutter_auth_service.dart` to:
```
lib/services/auth_service.dart
```

### 3b. Replace data_service.dart
Copy `flutter_data_service.dart` to:
```
lib/services/data_service.dart
```

### 3c. Update pubspec.yaml
Merge `flutter_pubspec.yaml` into your existing `pubspec.yaml`.
The key additions are:
```yaml
  sqflite: ^2.3.2
  path: ^1.9.0
```

### 3d. Run flutter pub get
```bash
flutter pub get
```

---

## STEP 4 — CONNECT ANDROID TO FLASK

### Android Emulator (default setup)
The base URL is already set correctly:
```dart
const String _base = 'http://10.0.2.2:5000/api/mobile';
```
`10.0.2.2` is the special IP that Android emulator uses to reach your PC's localhost.

### Physical Android Device
1. Connect your phone and PC to the same WiFi network
2. Find your PC's IP:
   - Windows: run `ipconfig` in CMD, look for IPv4 under your WiFi adapter
   - Mac/Linux: run `ifconfig | grep inet`
3. In both `flutter_auth_service.dart` and `flutter_data_service.dart`,
   change the `_base` constant to your PC's IP:
   ```dart
   static const String _base = 'http://192.168.1.5:5000/api/mobile';
   ```
   (replace 192.168.1.5 with your actual IP)
4. Also add this to `android/app/src/main/AndroidManifest.xml`
   inside the `<application>` tag:
   ```xml
   <uses-permission android:name="android.permission.INTERNET" />
   ```

### Allow cleartext HTTP (Android 9+)
In `android/app/src/main/AndroidManifest.xml`, in the `<application>` tag, add:
```xml
android:usesCleartextTraffic="true"
```

---

## STEP 5 — TEST THE FULL FLOW

### Default test accounts (password for all: Admin@123)
| Email                    | Status  | Role    |
|--------------------------|---------|---------|
| student@scholife.edu     | ACTIVE  | Student |
| maria@scholife.edu       | ACTIVE  | Student |
| jose@scholife.edu        | ACTIVE  | Student |

### Test login via Postman / curl
```bash
curl -X POST http://localhost:5000/api/mobile/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@scholife.edu","password":"Admin@123"}'
```
Expected response:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "student": { "id": 1, "full_name": "Juan dela Cruz", ... }
}
```

### Test protected endpoint (use the token from login)
```bash
curl http://localhost:5000/api/mobile/news/ \
  -H "Authorization: Bearer eyJ..."
```

---

## API REFERENCE

All endpoints (except /ping) require `Authorization: Bearer <token>` header.

### Auth
| Method | Endpoint                  | Body                                      | Description          |
|--------|---------------------------|-------------------------------------------|----------------------|
| POST   | /auth/register            | full_name, student_id, email, password    | Create account       |
| POST   | /auth/login               | email, password                           | Get JWT token        |
| GET    | /auth/me                  | —                                         | Current user profile |
| POST   | /auth/refresh             | —  (refresh token in header)              | Refresh access token |

### News
| Method | Endpoint                  | Query/Body                                | Description          |
|--------|---------------------------|-------------------------------------------|----------------------|
| GET    | /news/                    | ?category=all|health|academic|campus|sports | List articles      |
| GET    | /news/<id>                | —                                         | Single article       |
| POST   | /news/                    | title, body, category, is_featured        | Create article       |

### Events
| Method | Endpoint                  | Description          |
|--------|---------------------------|----------------------|
| GET    | /events/                  | List all events      |
| GET    | /events/<id>              | Single event         |
| POST   | /events/                  | Create event         |

### Clubs
| Method | Endpoint                  | Description          |
|--------|---------------------------|----------------------|
| GET    | /clubs/                   | List + is_joined flag|
| POST   | /clubs/<id>/join          | Join a club          |
| POST   | /clubs/<id>/leave         | Leave a club         |

### Marketplace
| Method | Endpoint                  | Description          |
|--------|---------------------------|----------------------|
| GET    | /marketplace/             | List active listings |
| GET    | /marketplace/?search=X    | Search listings      |
| POST   | /marketplace/             | Create listing       |
| PUT    | /marketplace/<id>         | Update (seller only) |
| DELETE | /marketplace/<id>         | Delete (seller only) |

### Lost & Found
| Method | Endpoint                  | Description          |
|--------|---------------------------|----------------------|
| GET    | /lost-found/              | All items            |
| GET    | /lost-found/?status=lost  | Filter by status     |
| POST   | /lost-found/              | Report item          |
| PUT    | /lost-found/<id>          | Update / resolve     |

### Chat
| Method | Endpoint                                     | Description          |
|--------|----------------------------------------------|----------------------|
| GET    | /chat/conversations                          | My conversations     |
| POST   | /chat/conversations                          | Start conversation   |
| GET    | /chat/conversations/<id>/messages            | Get messages         |
| POST   | /chat/conversations/<id>/messages            | Send message         |

### Leaderboard
| Method | Endpoint                  | Description          |
|--------|---------------------------|----------------------|
| GET    | /leaderboard/             | Top 50 by points     |

### Students
| Method | Endpoint                  | Description          |
|--------|---------------------------|----------------------|
| GET    | /students/profile         | My profile           |
| PUT    | /students/profile         | Update contact/avatar|

---

## SQLITE OFFLINE CACHE (sqflite)

The Flutter `data_service.dart` automatically:
1. Tries to fetch from Flask API
2. If successful → saves response to SQLite on-device
3. If network fails → loads from SQLite cache
4. If cache empty → falls back to mock data

Cache tables created in `scholife_cache.db`:
- `news_cache`
- `events_cache`
- `clubs_cache`
- `marketplace_cache`
- `lost_found_cache`
- `leaderboard_cache`

Cache is considered "fresh" for 10 minutes (configurable in `LocalDb.isCacheFresh`).

---

## COMMON ERRORS & FIXES

### "Connection refused" on emulator
- Make sure Flask is running (`python run.py`)
- Use `10.0.2.2:5000`, NOT `localhost:5000` in Flutter

### "Access denied for user 'root'@'localhost'"
- Set the correct DB_PASS in PyCharm run configuration
- Or edit `app/config.py` directly: `DB_PASS = 'your_password'`

### "ModuleNotFoundError: No module named 'flask'"
- Make sure your virtual environment is active in PyCharm
- Run `pip install -r requirements.txt` again

### "1045 Access denied" MySQL error
- Your MySQL root password is wrong in config.py

### Flutter: "SocketException: Failed host lookup"
- On physical device: change `_base` to your PC's LAN IP
- On emulator: confirm Flask is running and using `10.0.2.2`

### JWT token expired
- Tokens expire after 7 days — user must log in again
- Or implement refresh token logic in `AuthService`
