import sqlalchemy as sa
import os

HOST     = os.environ.get("DB_HOST", "localhost")
PORT     = int(os.environ.get("DB_PORT", 3306))
USER     = os.environ.get("DB_USER", "root")
PASSWORD = os.environ.get("DB_PASSWORD", "")
DATABASE = os.environ.get("DB_NAME", "school_db")

engine = sa.create_engine(
    f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}:{PORT}", echo=False)

SQL = f"""
CREATE DATABASE IF NOT EXISTS {DATABASE}
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE {DATABASE};

CREATE TABLE IF NOT EXISTS student (
    student_id   INT          PRIMARY KEY,
    student_code VARCHAR(50)  NOT NULL,
    gender       VARCHAR(5)   NOT NULL,
    major        VARCHAR(100) DEFAULT NULL,
    UNIQUE KEY uk_student_code (student_code)
);

CREATE TABLE IF NOT EXISTS subject (
    subject_id   INT          PRIMARY KEY,
    subject_code VARCHAR(50)  NOT NULL,
    subject_name VARCHAR(200) NOT NULL,
    UNIQUE KEY uk_subject_code (subject_code)
);

CREATE TABLE IF NOT EXISTS score (
    score_id    INT         PRIMARY KEY,
    student_id  INT         NOT NULL,
    subject_id  INT         NOT NULL,
    semester    VARCHAR(20) NOT NULL,
    grade       VARCHAR(5)  NOT NULL,
    grade_point FLOAT       NOT NULL,
    KEY idx_student (student_id),
    KEY idx_subject (subject_id),
    KEY idx_semester (semester)
);
"""

with engine.connect() as conn:
    for stmt in SQL.strip().split(';'):
        stmt = stmt.strip()
        if stmt:
            conn.execute(sa.text(stmt))
    # เพิ่ม column major ถ้ายังไม่มี (สำหรับ DB เดิมที่สร้างไว้แล้ว)
    try:
        conn.execute(sa.text(f"USE {DATABASE}"))
        conn.execute(sa.text("ALTER TABLE student ADD COLUMN major VARCHAR(100) DEFAULT NULL"))
        conn.commit()
        print("✓ เพิ่ม column major สำเร็จ")
    except Exception:
        conn.commit()
        print("✓ column major มีอยู่แล้ว")

print("✓ Database school_db พร้อมใช้งาน")