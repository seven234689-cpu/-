# CS Academic Performance Dashboard

## ລະບົບວິເຄາະແນວໂນ້ມຜົນການຮຽນ · ສາຂາວິທະຍາສາດຄອມພິວເຕີ

---

## ໂຄງສ້າງໂປຣເຈັກ

```
CS_Dashboard/
├── app.py                      ← รันตัวนี้เพื่อเปิด Dashboard (Flask + Dash)
├── db.py                       ← เชื่อมต่อ MySQL + โหลดข้อมูล + K-Means clustering
├── auth.py                     ← ตรวจสอบ login / hash password (salt จาก .env)
├── requirements.txt            ← library ที่ต้องติดตั้ง
├── render.yaml                 ← config สำหรับ deploy บน Render
│
├── pages/
│   ├── login.py                ← หน้าเข้าสู่ระบบ
│   ├── dashboard.py            ← หน้า Dashboard กราฟสรุปรวม
│   ├── search.py                ← หน้าค้นหานักศึกษารายคน
│   ├── predict.py              ← หน้าทำนาย GPA (Random Forest + XGBoost)
│   └── admin.py                ← หน้า Admin: เพิ่ม/ลบ นักศึกษา-วิชา, import .xlsx, reset, backup
│
├── ml/                          ← Pipeline การเทรนโมเดลทำนาย GPA
│   ├── data_prep.py            ← เตรียมข้อมูล + แบ่ง Stage (k=1..7 ภาคที่รู้แล้ว)
│   ├── train.py                ← เทรน RandomForest + XGBoost (GridSearchCV, K-Fold CV)
│   └── predictor.py            ← GPAPredictor class — โหลด/ทำนาย/ประเมินผล
│
├── models/                      ← ไฟล์โมเดลที่เทรนแล้ว (gpa_predictor.pkl)
├── backups/                     ← ไฟล์ backup .xlsx (สร้างอัตโนมัติก่อน Reset)
├── assets/                      ← รูปภาพ, ไอคอน, mobile.css
│
└── scripts/
    ├── setup_db.py              ← สร้างตาราง MySQL ครั้งแรก
    ├── import_csv.py            ← import ข้อมูลจาก CSV (ใช้ตอน setup เริ่มต้นเท่านั้น)
    ├── train_model.py           ← เทรนโมเดลทำนาย GPA ใหม่จากฐานข้อมูลปัจจุบัน
    ├── find_optimal_k.py        ← หาจำนวนกลุ่ม (k) ที่เหมาะสมสำหรับ K-Means
    └── export_report_figures.py ← export กราฟ/รูปสำหรับใส่ในรายงาน
```

> ⚠️ การ import ข้อมูลนักศึกษา/คะแนนประจำวันให้ทำผ่าน**หน้า Admin ในระบบ** (อัปโหลดไฟล์ `.xlsx`) ไม่ต้องใช้ `scripts/import_csv.py` แล้ว — สคริปต์นี้เก็บไว้สำหรับตอน setup ฐานข้อมูลใหม่ทั้งหมดเท่านั้น

---

## ขั้นตอนการใช้งาน (ติดตั้งครั้งแรก)

### 1. ติดตั้ง Library
```
pip install -r requirements.txt
```

### 2. เปิด XAMPP แล้ว Start MySQL

### 3. สร้างไฟล์ `.env` ที่ root โปรเจกต์
```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=school_db
FLASK_SECRET_KEY=ใส่ค่าสุ่มของตัวเอง
PASSWORD_SALT=ใส่ค่าสุ่มของตัวเอง
```

### 4. สร้างตารางใน MySQL
```
python scripts/setup_db.py
```

### 5. Import ข้อมูลเริ่มต้น (ถ้ามีไฟล์ CSV อยู่แล้ว)
```
python scripts/import_csv.py
```
สำหรับการเพิ่มข้อมูลรอบถัดไป ให้อัปโหลดไฟล์ `.xlsx` ผ่านหน้า **Admin** ในระบบแทน

### 6. เทรนโมเดลทำนาย GPA (ครั้งแรก หรือหลังข้อมูลเปลี่ยน)

```
python scripts/train_model.py
```

(หน้า Admin ก็มีปุ่ม "🏆 ເທຣນໂມເດລໃໝ່ທັງໝົด" ให้เทรนใหม่ได้โดยตรงในระบบเช่นกัน)

### 7. รัน Dashboard
```
python app.py
```
เปิด Browser ไปที่ http://127.0.0.1:8050

---

## การตั้งค่า Database

ค่าทั้งหมดอ่านจากไฟล์ `.env` (ดู [db.py](db.py)) ไม่ฮาร์ดโค้ดในไฟล์โค้ดอีกแล้ว เพื่อความปลอดภัยตอน deploy จริง

```python
HOST     = os.environ.get("DB_HOST", "localhost")
PORT     = int(os.environ.get("DB_PORT", 3306))
USER     = os.environ.get("DB_USER", "root")
PASSWORD = os.environ.get("DB_PASSWORD", "")
DATABASE = os.environ.get("DB_NAME", "school_db")
```

---

## ฟีเจอร์หลักของระบบ

- **Dashboard** — สรุป KPI รวม, กราฟแนวโน้ม GPA, สัดส่วนกลุ่มเสี่ยง (K-Means)
- **ค้นหานักศึกษา** — ดู GPA Trend และเกรดทุกวิชาของนักศึกษารายคน
- **ทำนาย GPA** — ทำนายผลการเรียนภาคที่เหลือจากภาคที่รู้แล้ว ด้วย RandomForest + XGBoost
- **Admin** — เพิ่ม/ลบนักศึกษา-วิชา, แก้เกรด, import/export Excel, Reset ระบบ (มี backup อัตโนมัติก่อนลบ), ดูประวัติการ import

## Deploy

โปรเจกต์นี้ตั้งค่าให้ deploy บน [Render](https://render.com) ผ่าน `render.yaml` — ตัวแปร environment (`DB_HOST`, `DB_PASSWORD`, `FLASK_SECRET_KEY`, `PASSWORD_SALT` ฯลฯ) ต้องตั้งค่าใน Render Dashboard เอง ไม่ commit ค่าจริงไว้ในโค้ด
