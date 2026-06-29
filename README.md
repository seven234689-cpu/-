# CS Academic Performance Dashboard

## ລະບົບວິເຄາະແນວໂນ້ມຜົນການຮຽນ · ສາຂາວິທະຍາສາດຄອມພິວເຕີ

---

## ໂຄງສ້າງໂປຣເຈັກ

```
CS_Dashboard/
├── app.py                      ← ລັນຕົວນີ້ເພື່ອເປີດ Dashboard (Flask + Dash)
├── db.py                       ← ເຊື່ອມຕໍ່ MySQL + ໂຫຼດຂໍ້ມູນ + K-Means clustering
├── auth.py                     ← ກວດສອບ login / hash password (salt ຈາກ .env)
├── requirements.txt            ← library ທີ່ຕ້ອງຕິດຕັ້ງ
├── render.yaml                 ← config ສຳລັບ deploy ເທິງ Render
│
├── pages/
│   ├── login.py                ← ໜ້າເຂົ້າສູ່ລະບົບ / ລົງທະບຽນ
│   ├── dashboard.py            ← ໜ້າ Dashboard ສະຫຼຸບກຣາຟລວມ
│   ├── search.py                ← ໜ້າຄົ້ນຫານັກສຶກສາລາຍຄົນ
│   ├── predict.py              ← ໜ້າຄາດຄະເນ GPA (Random Forest + XGBoost)
│   └── admin.py                ← ໜ້າ Admin: ເພີ່ມ/ລຶບ ນັກສຶກສາ-ວິຊາ, import .xlsx, reset, backup
│
├── ml/                          ← Pipeline ການເທຣນແບບຈຳລອງຄາດຄະເນ GPA
│   ├── data_prep.py            ← ກະກຽມຂໍ້ມູນ + ແບ່ງ Stage (k=1..7 ພາກທີ່ຮູ້ແລ້ວ)
│   ├── train.py                ← ເທຣນ RandomForest + XGBoost (GridSearchCV, K-Fold CV)
│   └── predictor.py            ← GPAPredictor class — ໂຫຼດ/ຄາດຄະເນ/ປະເມີນຜົນ
│
├── models/                      ← ໄຟລ໌ແບບຈຳລອງທີ່ເທຣນແລ້ວ (gpa_predictor.pkl)
├── backups/                     ← ໄຟລ໌ backup .xlsx (ສ້າງອັດຕະໂນມັດກ່ອນ Reset)
├── assets/                      ← ຮູບພາບ, ໄອຄອນ, mobile.css
├── report_figures/              ← ກຣາຟ/ຮູບທີ່ export ໄວ້ສຳລັບໃສ່ໃນບົດລາຍງານ
│
└── scripts/
    ├── setup_db.py                    ← ສ້າງຕາຕະລາງ MySQL ຄັ້ງທຳອິດ
    ├── import_csv.py                  ← import ຂໍ້ມູນຈາກ CSV (ໃຊ້ຕອນ setup ເລີ່ມຕົ້ນເທົ່ານັ້ນ)
    ├── train_model.py                 ← ເທຣນແບບຈຳລອງຄາດຄະເນ GPA ໃໝ່ຈາກຖານຂໍ້ມູນປັດຈຸບັນ
    ├── find_optimal_k.py              ← ຊອກຫາຈຳນວນກຸ່ມ (k) ທີ່ເໝາະສົມສຳລັບ K-Means
    ├── export_report_figures.py       ← export ກຣາຟຈາກ Dashboard (heatmap, correlation, donut, ...)
    ├── export_model_eval_figures.py   ← export ກຣາຟ Scatter ແລະ Feature Importance ຂອງ RF/XGBoost
    ├── export_colab_style_fig.py      ← export ຮູບສະຕາຍ Colab (ໂຄ້ດ + ຜົນຮັບ) ສຳລັບບົດລາຍງານ
    ├── export_donut_code_fig.py       ← export ຮູບສະຕາຍ VS Code ຂອງໂຄ້ດ Donut Chart
    ├── export_kmeans_trend_fig.py     ← export ກຣາຟແນວໂນ້ມ GPA ຕາມກຸ່ມ K-Means
    └── nested_cv_eval.py              ← ປະເມີນ Nested Cross-Validation ກວດສອບຄວາມໜ້າເຊື່ອຖືຂອງຄ່າ RMSE/MAE
```

> ⚠️ ການ import ຂໍ້ມູນນັກສຶກສາ/ຄະແນນປະຈຳວັນໃຫ້ເຮັດຜ່ານ**ໜ້າ Admin ໃນລະບົບ** (ອັປໂຫຼດໄຟລ໌ `.xlsx`) ບໍ່ຕ້ອງໃຊ້ `scripts/import_csv.py` ແລ້ວ — ສະຄຣິບນີ້ເກັບໄວ້ສຳລັບຕອນ setup ຖານຂໍ້ມູນໃໝ່ທັງໝົດເທົ່ານັ້ນ

---

## ຂັ້ນຕອນການນຳໃຊ້ (ຕິດຕັ້ງຄັ້ງທຳອິດ)

### 1. ຕິດຕັ້ງ Library
```
pip install -r requirements.txt
```

### 2. ເປີດ XAMPP ແລ້ວ Start MySQL

### 3. ສ້າງໄຟລ໌ `.env` ທີ່ root ໂປຣເຈັກ

```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=school_db
FLASK_SECRET_KEY=ໃສ່ຄ່າສຸ່ມຂອງຕົນເອງ
PASSWORD_SALT=ໃສ່ຄ່າສຸ່ມຂອງຕົນເອງ
```

### 4. ສ້າງຕາຕະລາງໃນ MySQL

```
python scripts/setup_db.py
```

### 5. Import ຂໍ້ມູນເລີ່ມຕົ້ນ (ຖ້າມີໄຟລ໌ CSV ຢູ່ແລ້ວ)
```
python scripts/import_csv.py
```
ສຳລັບການເພີ່ມຂໍ້ມູນຮອບຖັດໄປ ໃຫ້ອັປໂຫຼດໄຟລ໌ `.xlsx` ຜ່ານໜ້າ **Admin** ໃນລະບົບແທນ

### 6. ເທຣນແບບຈຳລອງຄາດຄະເນ GPA (ຄັ້ງທຳອິດ ຫຼື ຫຼັງຂໍ້ມູນປ່ຽນ)

```
python scripts/train_model.py
```

(ໜ້າ Admin ກໍ່ມີປຸ່ມ "🏆 ເທຣນໂມເດລໃໝ່ທັງໝົດ" ໃຫ້ເທຣນໃໝ່ໄດ້ໂດຍກົງໃນລະບົບເຊັ່ນກັນ)

### 7. ລັນ Dashboard
```
python app.py
```
ເປີດ Browser ໄປທີ່ http://127.0.0.1:8050

---

## ການຕັ້ງຄ່າ Database

ຄ່າທັງໝົດອ່ານຈາກໄຟລ໌ `.env` (ເບິ່ງ [db.py](db.py)) ບໍ່ Hard-code ໃນໄຟລ໌ໂຄ້ດອີກແລ້ວ ເພື່ອຄວາມປອດໄພຕອນ deploy ຈິງ

```python
HOST     = os.environ.get("DB_HOST", "localhost")
PORT     = int(os.environ.get("DB_PORT", 3306))
USER     = os.environ.get("DB_USER", "root")
PASSWORD = os.environ.get("DB_PASSWORD", "")
DATABASE = os.environ.get("DB_NAME", "school_db")
```

---

## ຄຸນສົມບັດຫຼັກຂອງລະບົບ

- **Dashboard** — ສະຫຼຸບ KPI ລວມ, ກຣາຟແນວໂນ້ມ GPA, ສັດສ່ວນກຸ່ມສ່ຽງ (K-Means)
- **ຄົ້ນຫານັກສຶກສາ** — ເບິ່ງ GPA Trend ແລະ ເກຣດທຸກວິຊາຂອງນັກສຶກສາລາຍຄົນ
- **ຄາດຄະເນ GPA** — ຄາດຄະເນຜົນການຮຽນພາກທີ່ເຫຼືອຈາກພາກທີ່ຮູ້ແລ້ວ ດ້ວຍ RandomForest + XGBoost
- **Admin** — ເພີ່ມ/ລຶບນັກສຶກສາ-ວິຊາ, ແກ້ເກຣດ, import/export Excel, Reset ລະບົບ (ມີ backup ອັດຕະໂນມັດກ່ອນລຶບ), ເບິ່ງປະຫວັດການ import

## Deploy

ໂປຣເຈັກນີ້ຕັ້ງຄ່າໃຫ້ deploy ເທິງ [Render](https://render.com) ຜ່ານ `render.yaml` — ຕົວປ່ຽນ environment (`DB_HOST`, `DB_PASSWORD`, `FLASK_SECRET_KEY`, `PASSWORD_SALT` ຯລຯ) ຕ້ອງຕັ້ງຄ່າໃນ Render Dashboard ເອງ ບໍ່ commit ຄ່າຈິງໄວ້ໃນໂຄ້ດ
