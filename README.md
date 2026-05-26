# CS Academic Performance Dashboard
## ລະບົບວິເຄາະຜົນການຮຽນ · ສາຂາວິທະຍາສາດຄອມພິວເຕີ

---

## ໂຄງສ້າງໂປຣເຈັກ

```
CS_Dashboard/
├── app.py                  ← รันตัวนี้เพื่อเปิด Dashboard
├── db.py                   ← เชื่อมต่อ MySQL + โหลดข้อมูล
├── requirements.txt        ← library ที่ต้องติดตั้ง
├── pages/
│   ├── __init__.py
│   ├── dashboard.py        ← หน้า Dashboard กราฟ
│   ├── search.py           ← หน้าค้นหานักศึกษา
│   └── admin.py            ← หน้า Admin จัดการข้อมูล
├── csv_data/               ← วาง CSV ไฟล์ที่นี่
│   ├── Student.csv
│   ├── Subject.csv
│   └── Score.csv
└── scripts/
    ├── setup_db.py         ← สร้างตาราง MySQL
    └── import_csv.py       ← import CSV เข้า MySQL
```

---

## ขั้นตอนการใช้งาน

### 1. ติดตั้ง Library
```
pip install -r requirements.txt
```

### 2. เปิด XAMPP แล้ว Start MySQL

### 3. สร้างตารางใน MySQL
```
python scripts/setup_db.py
```

### 4. Import ข้อมูลจาก CSV
```
python scripts/import_csv.py
```

### 5. รัน Dashboard
```
python app.py
```
เปิด Browser ไปที่ http://127.0.0.1:8050

---

## การตั้งค่า Database (db.py)
```python
HOST     = "localhost"
PORT     = 3306
USER     = "root"
PASSWORD = ""          # XAMPP ส่วนใหญ่ว่างเปล่า
DATABASE = "school_db"
```
