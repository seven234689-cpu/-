# ============================================================
#  scripts/setup_db.py
#  สร้างตาราง MySQL ทั้งหมด (รันครั้งเดียว)
# ============================================================

import sqlalchemy as sa

HOST     = "localhost"
PORT     = 3306
USER     = "root"
PASSWORD = ""          # ← แก้ถ้ามี password
DATABASE = "school_db"

engine = sa.create_engine(
    f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}:{PORT}",
    echo=False
)

SQL = f"""
-- สร้าง Database
CREATE DATABASE IF NOT EXISTS {DATABASE}
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE {DATABASE};

-- ตาราง Student
CREATE TABLE IF NOT EXISTS student (
    student_id   INT          PRIMARY KEY,
    student_code VARCHAR(50)  NOT NULL,
    gender       VARCHAR(5)   NOT NULL,
    UNIQUE KEY uk_student_code (student_code)
);

-- ตาราง Subject
CREATE TABLE IF NOT EXISTS subject (
    subject_id   INT          PRIMARY KEY,
    subject_code VARCHAR(50)  NOT NULL,
    subject_name VARCHAR(200) NOT NULL,
    UNIQUE KEY uk_subject_code (subject_code)
);

-- ตาราง Score
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
    conn.commit()

print("✓ สร้าง Database school_db สำเร็จ")
print("✓ สร้างตาราง student, subject, score สำเร็จ")
print("\nพร้อม import ข้อมูลแล้ว รัน:")
print("  python scripts/import_csv.py")
