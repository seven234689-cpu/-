# auth.py — Database Authentication Helper
import hashlib
import logging
import os
import sqlalchemy as sa
import db

logger = logging.getLogger(__name__)

# ใช้ SALT เดิมที่ตรงกับตอน register ครั้งแรก — เก็บไว้ใน .env (PASSWORD_SALT)
SALT = os.environ.get("PASSWORD_SALT", "cs_dashboard_2025")
DB_ERR_MSG = "ບໍ່ສາມາດເຊື່ອມຕໍ່ຖານຂໍ້ມູນໄດ້ ກະລຸນາລອງໃໝ່"

def _hash(pw):
    return hashlib.sha256((pw + SALT).encode()).hexdigest()

def init_users_table():
    with db.engine.connect() as conn:
        conn.execute(sa.text("""
            CREATE TABLE IF NOT EXISTS users (
                id            INT AUTO_INCREMENT PRIMARY KEY,
                email         VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role          VARCHAR(20) NOT NULL DEFAULT 'user',
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()
        # เพิ่มคอลัมน์ role ให้ตารางเก่าที่สร้างไว้ก่อนหน้านี้ (ถ้ายังไม่มี)
        col_exists = conn.execute(sa.text("""
            SELECT COUNT(*) AS c FROM information_schema.columns
            WHERE table_schema = DATABASE() AND table_name = 'users' AND column_name = 'role'
        """)).fetchone()[0]
        if not col_exists:
            conn.execute(sa.text("ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user'"))
            conn.commit()

def register_user(email, password):
    try:
        with db.engine.connect() as conn:
            if conn.execute(
                sa.text("SELECT id FROM users WHERE email=:e"),
                {"e": email.lower().strip()}
            ).fetchone():
                return False, "ອີເມລນີ້ຖືກໃຊ້ງານແລ້ວ"
            conn.execute(
                sa.text("INSERT INTO users (email,password_hash,role) VALUES (:e,:p,'user')"),
                {"e": email.lower().strip(), "p": _hash(password)}
            )
            conn.commit()
            return True, "ລົງທະບຽນສໍາເລັດ"
    except Exception:
        logger.exception('register_user failed for %s', email)
        return False, DB_ERR_MSG

def login_user(email, password):
    try:
        with db.engine.connect() as conn:
            row = conn.execute(
                sa.text("SELECT id, role FROM users WHERE email=:e AND password_hash=:p"),
                {"e": email.lower().strip(), "p": _hash(password)}
            ).fetchone()
            return (True, row.role) if row else (False, "ອີເມລ ຫຼື ລະຫັດຜ່ານບໍ່ຖືກຕ້ອງ")
    except Exception:
        logger.exception('login_user failed for %s', email)
        return False, DB_ERR_MSG

def get_role(email):
    try:
        with db.engine.connect() as conn:
            row = conn.execute(
                sa.text("SELECT role FROM users WHERE email=:e"),
                {"e": email.lower().strip()}
            ).fetchone()
            return row.role if row else None
    except Exception:
        return None

def reset_password(email, new_password):
    """ใช้ reset password ถ้า SALT เปลี่ยน"""
    try:
        with db.engine.connect() as conn:
            conn.execute(
                sa.text("UPDATE users SET password_hash=:p WHERE email=:e"),
                {"e": email.lower().strip(), "p": _hash(new_password)}
            )
            conn.commit()
            return True, "ລີເຊັດລະຫັດຜ່ານສໍາເລັດ"
    except Exception:
        logger.exception('reset_password failed for %s', email)
        return False, DB_ERR_MSG

try:
    init_users_table()
except Exception as e:
    print(f"[auth] {e}")