# ============================================================
#  scripts/import_csv.py
#  Import CSV ทั้งหมดเข้า MySQL (Student, Subject, Score)
#  รองรับการรันซ้ำ — ข้ามข้อมูลที่มีอยู่แล้ว
# ============================================================

import pandas as pd
import sqlalchemy as sa
import os

HOST     = "localhost"
PORT     = 3306
USER     = "root"
PASSWORD = ""          
DATABASE = "school_db"

engine = sa.create_engine(
    f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}",
    echo=False
)

CSV_DIR = os.path.join(os.path.dirname(__file__), '..', 'csv_data')

def import_table(csv_file, table, pk_col, insert_sql, row_fn):
    path = os.path.join(CSV_DIR, csv_file)
    if not os.path.exists(path):
        print(f"⚠  ไม่พบไฟล์ {csv_file} — ข้ามไป")
        return

    df = pd.read_csv(path, encoding='utf-8-sig')
    print(f"\n📄 {csv_file} : {len(df):,} rows")

    with engine.connect() as conn:
        existing = pd.read_sql(f"SELECT {pk_col} FROM {table}", conn)
        exist_set = set(existing[pk_col].tolist())

        new_rows = [row_fn(r) for _, r in df.iterrows()
                    if r[pk_col] not in exist_set]

        if not new_rows:
            print(f"   ✓ ข้อมูลครบแล้ว ไม่มีอะไรใหม่")
            return

        conn.execute(sa.text(insert_sql), new_rows)
        conn.commit()

    print(f"   ✓ เพิ่มใหม่ {len(new_rows):,} rows")
    print(f"   ⏭  ข้าม {len(df)-len(new_rows):,} rows (มีอยู่แล้ว)")


# ── Student ───────────────────────────────────────────────
import_table(
    csv_file   = 'Student.csv',
    table      = 'student',
    pk_col     = 'student_id',
    insert_sql = "INSERT INTO student (student_id, student_code, gender) "
                 "VALUES (:student_id, :student_code, :gender)",
    row_fn     = lambda r: {
        'student_id'  : int(r['student_id']),
        'student_code': str(r['student_code']).strip(),
        'gender'      : str(r['gender']).strip()
    }
)

# ── Subject ───────────────────────────────────────────────
import_table(
    csv_file   = 'Subject.csv',
    table      = 'subject',
    pk_col     = 'subject_id',
    insert_sql = "INSERT INTO subject (subject_id, subject_code, subject_name) "
                 "VALUES (:subject_id, :subject_code, :subject_name)",
    row_fn     = lambda r: {
        'subject_id'  : int(r['subject_id']),
        'subject_code': str(r['subject_code']).strip(),
        'subject_name': str(r['subject_name']).strip()
    }
)

# ── Score ─────────────────────────────────────────────────
import_table(
    csv_file   = 'Score.csv',
    table      = 'score',
    pk_col     = 'score_id',
    insert_sql = "INSERT INTO score (score_id, student_id, subject_id, semester, grade, grade_point) "
                 "VALUES (:score_id, :student_id, :subject_id, :semester, :grade, :grade_point)",
    row_fn     = lambda r: {
        'score_id'   : int(r['score_id']),
        'student_id' : int(r['student_id']),
        'subject_id' : int(r['subject_id']),
        'semester'   : str(r['semester']).strip(),
        'grade'      : str(r['grade']).strip(),
        'grade_point': float(r['grade_point'])
    }
)

# ── สรุปผล ────────────────────────────────────────────────
print("\n" + "="*40)
with engine.connect() as conn:
    for tbl in ['student','subject','score']:
        n = pd.read_sql(f"SELECT COUNT(*) AS c FROM {tbl}", conn)['c'].iloc[0]
        print(f"  {tbl:12} : {n:>8,} rows")
print("="*40)
print("✅ Import เสร็จสมบูรณ์")
print("\nรัน Dashboard ได้เลย:")
print("  python app.py")
