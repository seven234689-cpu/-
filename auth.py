# auth.py — Database Authentication Helper
import hashlib
import os
import sqlalchemy as sa
import db

# ใช้ SALT เดิมที่ตรงกับตอน register ครั้งแรก — เก็บไว้ใน .env (PASSWORD_SALT)
SALT = os.environ.get("PASSWORD_SALT", "cs_dashboard_2025")

def _hash(pw):
    return hashlib.sha256((pw + SALT).encode()).hexdigest()

def init_users_table():
    with db.engine.connect() as conn:
        conn.execute(sa.text("""
            CREATE TABLE IF NOT EXISTS users (
                id            INT AUTO_INCREMENT PRIMARY KEY,
                email         VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
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
                sa.text("INSERT INTO users (email,password_hash) VALUES (:e,:p)"),
                {"e": email.lower().strip(), "p": _hash(password)}
            )
            conn.commit()
            return True, "ລົງທະບຽນສໍາເລັດ"
    except Exception as ex:
        return False, str(ex)

def login_user(email, password):
    try:
        with db.engine.connect() as conn:
            row = conn.execute(
                sa.text("SELECT id FROM users WHERE email=:e AND password_hash=:p"),
                {"e": email.lower().strip(), "p": _hash(password)}
            ).fetchone()
            return (True, "OK") if row else (False, "ອີເມລ ຫຼື ລະຫັດຜ່ານບໍ່ຖືກຕ້ອງ")
    except Exception as ex:
        return False, str(ex)

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
    except Exception as ex:
        return False, str(ex)

try:
    init_users_table()
except Exception as e:
    print(f"[auth] {e}")