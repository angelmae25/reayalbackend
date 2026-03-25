# =============================================================================
# app/config.py  —  All configuration in one place
# =============================================================================

import os
from datetime import timedelta


class Config:
    # ── MySQL Database ─────────────────────────────────────────────────────────
    # Edit DB_USER / DB_PASS / DB_HOST to match your MySQL setup in PyCharm.
    # PyCharm typically runs MySQL on localhost:3306.
    DB_USER = os.environ.get('DB_USER',  'root')
    DB_PASS = os.environ.get('DB_PASS',  '1234')        # ← change to your MySQL password
    DB_HOST = os.environ.get('DB_HOST',  'localhost')
    DB_PORT = os.environ.get('DB_PORT',  '3306')
    DB_NAME = os.environ.get('DB_NAME',  'Schoolifetrue_db')

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        f"?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False   # set True to log SQL queries during dev

    # ── JWT ───────────────────────────────────────────────────────────────────
    # Change SECRET_KEY to any long random string in production!
    SECRET_KEY          = os.environ.get('SECRET_KEY', 'scholife-super-secret-key-2024')
    JWT_SECRET_KEY      = os.environ.get('JWT_SECRET_KEY', 'scholife-jwt-secret-2024')
    JWT_ACCESS_TOKEN_EXPIRES  = timedelta(days=7)   # token lives 7 days
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # ── General ───────────────────────────────────────────────────────────────
    DEBUG = True
    TESTING = False

    # ── Allow large JSON bodies for base64 image uploads (10 MB) ─────────────
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB