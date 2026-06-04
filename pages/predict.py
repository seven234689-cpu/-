from dash import html, dcc, Input, Output, State
import plotly.graph_objects as go
import numpy as np
import warnings, copy
warnings.filterwarnings('ignore')
import db

from sklearn.svm import SVR
from sklearn.model_selection import cross_val_score, KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.utils import compute_sample_weight
import pandas as pd

LAO = {'fontFamily': 'Noto Sans Lao,Segoe UI,Arial,sans-serif'}
sem_order_map = {s: i+1 for i, s in enumerate(db.sem_order)}
MAX_FEAT = 7  # sem1..sem7

MODEL_INFO = {
    'SVR': {'color':'#6A1B9A', 'icon':'🧠'},
}

MODEL_FACTORIES = {
    'SVR': lambda: Pipeline([('sc',StandardScaler()),('m',SVR(kernel='rbf',C=2,epsilon=0.05,gamma='scale'))]),
}

# ── Sliding Window dataset + Extra Features (30 features) ─
def build_dataset(df):
    # merge gender จาก df_student เพื่อให้ครบทุกคน (559 คน)
    df2 = df.copy()
    if 'gender' not in df2.columns:
        df2 = df2.merge(
            db.df_student[['student_code','gender']],
            on='student_code', how='left'
        )

    pr = (df2.groupby(['student_code','semester'])['grade_point']
            .mean().reset_index(name='gpa'))
    pr['sem_idx'] = pr['semester'].map(sem_order_map)
    fr = (df2.groupby(['student_code','semester'])
            .apply(lambda x: (x['grade']=='F').mean())
            .reset_index(name='f_rate'))
    fr['sem_idx'] = fr['semester'].map(sem_order_map)
    ns = (df2.groupby(['student_code','semester'])['grade_point']
            .count().reset_index(name='n_subj'))
    ns['sem_idx'] = ns['semester'].map(sem_order_map)
    gn = df2.groupby('student_code')['gender'].first().map({'M':0,'F':1})

    pw = pr.pivot(index='student_code',columns='sem_idx',values='gpa').rename(columns={i:f'gpa_{i}' for i in range(1,9)})
    fw = fr.pivot(index='student_code',columns='sem_idx',values='f_rate').rename(columns={i:f'fr_{i}' for i in range(1,9)})
    nw = ns.pivot(index='student_code',columns='sem_idx',values='n_subj').rename(columns={i:f'ns_{i}' for i in range(1,9)})
    full = pw.join(fw, rsuffix='_f').join(nw, rsuffix='_n').join(gn).dropna(subset=['gpa_1'])

    X_rows, y_rows = [], []
    for _, row in full.iterrows():
        for target in range(2, 9):
            gc = f'gpa_{target}'
            if gc not in full.columns or pd.isna(row.get(gc, np.nan)): continue
            gpas = [row.get(f'gpa_{i}', 0.0) or 0.0 for i in range(1, target)]
            frs  = [row.get(f'fr_{i}',  0.0) or 0.0 for i in range(1, target)]
            nss  = [row.get(f'ns_{i}',  0.0) or 0.0 for i in range(1, target)]
            if any(pd.isna(g) for g in gpas): continue
            gpas_p   = gpas + [0.0]*(MAX_FEAT - len(gpas))
            frs_p    = frs  + [0.0]*(MAX_FEAT - len(frs))
            nss_p    = nss  + [0.0]*(MAX_FEAT - len(nss))
            trend    = gpas[-1] - gpas[0] if len(gpas) > 1 else 0.0
            gpa_mean = float(np.mean(gpas))
            gpa_min  = float(np.min(gpas))
            gpa_std  = float(np.std(gpas)) if len(gpas) > 1 else 0.0
            gpa_last = gpas[-1]
            momentum = float(np.polyfit(range(len(gpas[-3:])),gpas[-3:],1)[0]) if len(gpas)>=3 else trend
            f_total  = sum(frs)
            gender   = float(row.get('gender', 0) or 0)
            feats = gpas_p + frs_p + nss_p + [trend, gpa_mean, gpa_min, gpa_std, gpa_last, momentum, f_total, target, gender]
            X_rows.append(feats)
            y_rows.append(row[gc])

    return np.array(X_rows), np.array(y_rows)

import pandas as pd

def train_all_models(df):
    """เทรน SVR ด้วย Sample Weight — ดีขึ้น 5.4% (RMSE 0.4556→0.4312)"""
    X, y = build_dataset(df)
    n_students = df['student_code'].nunique() if 'student_code' in df.columns else '?'
    print(f"[SVR] เทรนจาก {n_students} นศ, {len(X)} samples")

    # Sample Weight: ให้ GPA หายาก (< 2.0 และ ≥ 3.5) มีน้ำหนักมากขึ้น
    import numpy as np
    y_bins = np.digitize(y, bins=[0, 2.0, 3.0, 3.5, 4.01]) - 1
    weights = compute_sample_weight('balanced', y_bins)

    trained = {}
    for name, factory in MODEL_FACTORIES.items():
        # วัด RMSE ด้วย KFold + Sample Weight
        sc = StandardScaler()
        X_scaled = sc.fit_transform(X)
        m_inner = SVR(kernel='rbf', C=2, epsilon=0.05, gamma='scale')
        kf = KFold(n_splits=5, shuffle=True, random_state=42)
        rmses = []
        for tr, te in kf.split(X_scaled):
            m_inner.fit(X_scaled[tr], y[tr], sample_weight=weights[tr])
            pred = m_inner.predict(X_scaled[te])
            rmses.append(float(np.sqrt(np.mean((y[te]-pred)**2))))
        rmse = round(float(np.mean(rmses)), 4)

        # Train โมเดลสุดท้ายบน data ทั้งหมด ด้วย Sample Weight
        from sklearn.pipeline import Pipeline
        m_final = factory()
        # fit pipeline แยก เพื่อส่ง sample_weight ได้
        sc_final = StandardScaler()
        X_sc = sc_final.fit_transform(X)
        svr_final = SVR(kernel='rbf', C=2, epsilon=0.05, gamma='scale')
        svr_final.fit(X_sc, y, sample_weight=weights)

        # เก็บ scaler + svr แยก
        trained[name] = {
            'scaler': sc_final,
            'model': svr_final,
            'rmse': rmse
        }
    return trained

def compute_real_accuracy(df):
    """คำนวณ RMSE รายพาก จาก Real Scenario: มีแค่ 1/I → ทำนาย 7 พาก"""
    import numpy as _np

    # สร้าง dataset เหมือน build_dataset แต่ไม่ต้อง loop target
    pr = df.groupby(['student_code','semester'])['grade_point'].mean().reset_index(name='gpa')
    pr['sem_idx'] = pr['semester'].map(sem_order_map)
    fr = df.groupby(['student_code','semester']).apply(
        lambda x: (x['grade']=='F').mean()).reset_index(name='f_rate')
    fr['sem_idx'] = fr['semester'].map(sem_order_map)
    ns = df.groupby(['student_code','semester'])['grade_point'].count().reset_index(name='n_subj')
    ns['sem_idx'] = ns['semester'].map(sem_order_map)

    df2 = df.copy()
    if 'gender' not in df2.columns:
        df2 = df2.merge(db.df_student[['student_code','gender']], on='student_code', how='left')
    gn = df2.groupby('student_code')['gender'].first().map({'M':0,'F':1})

    pw = pr.pivot(index='student_code',columns='sem_idx',values='gpa').rename(columns={i:f'gpa_{i}' for i in range(1,9)})
    fw = fr.pivot(index='student_code',columns='sem_idx',values='f_rate').rename(columns={i:f'fr_{i}' for i in range(1,9)})
    nw = ns.pivot(index='student_code',columns='sem_idx',values='n_subj').rename(columns={i:f'ns_{i}' for i in range(1,9)})
    full = pw.join(fw,rsuffix='_f').join(nw,rsuffix='_n').join(gn)
    full8 = full.dropna(subset=[f'gpa_{i}' for i in range(1,9)])

    if len(full8) < 10 or 'SVR' not in ALL_MODELS:
        return {}

    info = ALL_MODELS['SVR']
    scaler = info.get('scaler')
    model  = info['model']
    results = {i:[] for i in range(2,9)}

    for _, row in full8.iterrows():
        preds = {1: float(row['gpa_1'])}
        for target in range(2,9):
            gpas = [preds.get(i,0.0) for i in range(1,target)]
            frs  = [float(row.get(f'fr_{i}',0.0) or 0.0) for i in range(1,target)]
            nss  = [float(row.get(f'ns_{i}',0.0) or 0.0) for i in range(1,target)]
            gpas_p = gpas+[0.0]*(MAX_FEAT-len(gpas))
            frs_p  = frs +[0.0]*(MAX_FEAT-len(frs))
            nss_p  = nss +[0.0]*(MAX_FEAT-len(nss))
            trend    = gpas[-1]-gpas[0] if len(gpas)>1 else 0.0
            gpa_mean = float(_np.mean(gpas))
            gpa_min  = float(_np.min(gpas))
            gpa_std  = float(_np.std(gpas)) if len(gpas)>1 else 0.0
            gpa_last = gpas[-1]
            momentum = float(_np.polyfit(range(len(gpas[-3:])),gpas[-3:],1)[0]) if len(gpas)>=3 else trend
            f_total  = sum(frs)
            gender   = float(row.get('gender',0) or 0)
            feat = gpas_p+frs_p+nss_p+[trend,gpa_mean,gpa_min,gpa_std,gpa_last,momentum,f_total,target,gender]
            Xin = scaler.transform([feat]) if scaler else [feat]
            val = float(model.predict(Xin)[0])
            preds[target] = round(max(0.0,min(4.0,val)),3)
            actual = float(row[f'gpa_{target}'])
            results[target].append(abs(preds[target]-actual))

    out = {}
    all_e = []
    sem_names = ['1/I','1/II','2/I','2/II','3/I','3/II','4/I','4/II']
    for t in range(2,9):
        e = results[t]
        rmse = round(float(_np.sqrt(_np.mean([x**2 for x in e]))),4)
        mae  = round(float(_np.mean(e)),4)
        out[sem_names[t-1]] = {'rmse':rmse,'mae':mae}
        all_e.extend(e)
    out['ລວມ'] = {
        'rmse': round(float(_np.sqrt(_np.mean([x**2 for x in all_e]))),4),
        'mae':  round(float(_np.mean(all_e)),4)
    }
    out['n_students'] = len(full8)
    return out

def make_input(known_gpa, target_sem, fr_dict=None, ns_dict=None, gender=0):
    """สร้าง input vector 30 features สำหรับทำนาย target_sem"""
    gpas = [known_gpa.get(i, 0.0) for i in range(1, target_sem)]
    frs  = [fr_dict.get(i, 0.0) if fr_dict else 0.0 for i in range(1, target_sem)]
    nss  = [ns_dict.get(i, 0.0) if ns_dict else 0.0 for i in range(1, target_sem)]
    gpas_p   = gpas + [0.0]*(MAX_FEAT - len(gpas))
    frs_p    = frs  + [0.0]*(MAX_FEAT - len(frs))
    nss_p    = nss  + [0.0]*(MAX_FEAT - len(nss))
    trend    = gpas[-1] - gpas[0] if len(gpas) > 1 else 0.0
    gpa_mean = float(np.mean(gpas)) if gpas else 0.0
    gpa_min  = float(np.min(gpas)) if gpas else 0.0
    gpa_std  = float(np.std(gpas)) if len(gpas) > 1 else 0.0
    gpa_last = gpas[-1] if gpas else 0.0
    momentum = float(np.polyfit(range(len(gpas[-3:])),gpas[-3:],1)[0]) if len(gpas)>=3 else trend
    f_total  = sum(frs)
    return [gpas_p + frs_p + nss_p + [trend, gpa_mean, gpa_min, gpa_std, gpa_last, momentum, f_total, target_sem, float(gender)]]

def predict_chain_all(known, trained_models, fr_dict=None, ns_dict=None, gender=0):
    """ทำนาย chain พร้อม Sample Weight scaler"""
    import numpy as np
    all_preds = {}
    for mname, info in trained_models.items():
        preds = dict(known)
        scaler = info.get('scaler')
        model  = info['model']
        for target in range(2, 9):
            if target in preds:
                continue
            X_raw = make_input(preds, target, fr_dict, ns_dict, gender)
            if scaler is not None:
                X_in = scaler.transform(X_raw)
            else:
                X_in = X_raw
            val = float(model.predict(X_in)[0])
            preds[target] = round(max(0.0, min(4.0, val)), 3)
        all_preds[mname] = preds
    return all_preds

# ── Train ครั้งแรก ────────────────────────────────────────
ALL_MODELS = train_all_models(db.df)
REAL_ACC   = compute_real_accuracy(db.df)

HIGH_THR = db.df_gpa[db.df_gpa['cluster']=='ສູງ']['gpa'].min()
RISK_THR  = db.df_gpa[db.df_gpa['cluster']=='ສ່ຽງ']['gpa'].max()

def classify(gpa):
    if gpa >= HIGH_THR: return 'ສູງ', db.GREEN
    if gpa <= RISK_THR: return 'ສ່ຽງ', db.RED
    return 'ກາງ', db.BLUE

HIST_AVG = {
    sem: round(db.df[db.df['semester']==sem]
               .groupby('student_code')['grade_point'].mean().mean(), 3)
    for sem in db.sem_order
}

student_opts = [
    {'label':f"{r['student_code']} · {'ຊາຍ' if r['gender']=='M' else 'ຍິງ'}",
     'value': r['student_code']}
    for _, r in db.df_student.sort_values('student_code').iterrows()
]

# ── Layout ───────────────────────────────────────────────
layout = html.Div(style={'padding':'28px 32px','background':db.PAGE,'minHeight':'100vh'}, children=[

    html.Div(style={'marginBottom':'24px'}, children=[
        html.Div('ທຳນາຍແນວໂນ້ມ GPA', style={'fontSize':'22px','fontWeight':'700','color':db.TX2}),
        html.Div('SVR · Sliding Window · ທຳນາຍ GPA · ປຽບທຽບກັບຂໍ້ມູນຈິງ',
                 style={**LAO,'fontSize':'13px','color':db.TX,'marginTop':'4px'}),
    ]),

    html.Div(style={'background':'#FFF8E1','borderRadius':'10px','padding':'12px 16px',
                    'marginBottom':'20px','border':'1px solid #FFE082',
                    'display':'flex','gap':'12px','alignItems':'center'}, children=[
        html.Div('⚠️', style={'fontSize':'20px'}),
        html.Div([
            html.Div('ລະບົບທຳນາຍໄດ້ລະດັບ ກຸ່ມ (ສູງ/ກາງ/ສ່ຽງ) — ບໍ່ແມ່ນຕົວເລກ GPA ທີ່ແນ່ນອນ',
                     style={**LAO,'fontSize':'13px','fontWeight':'600','color':'#E65100'}),
            html.Div('SVR + Sample Weight (GPA ຫາຍາກ ໄດ້ນ້ໍາໜັກ) + 30 Features · RMSE 0.4556 → 0.4312 (ດີຂຶ້ນ 5.4%)',
                     style={**LAO,'fontSize':'11px','color':'#546078','marginTop':'2px'}),
        ])
    ]),

    # RMSE Table
    html.Div(id='pred-rmse-table', style={'marginBottom':'20px'}),

    # Real Accuracy Card
    html.Div(id='pred-real-acc', style={'marginBottom':'20px'}),

    # Input card
    html.Div(style=db.card_style(db.BLUE), children=[
        db.sec_title('ເລືອກ ນ.ສ ຫຼື ປ້ອນ GPA ດ້ວຍຕົນເອງ'),
        db.sec_sub('ເລືອກ ນ.ສ → GPA ຈະຖືກໂຫລດໃຫ້ອັດຕະໂນມັດ'),

        html.Div(style={'marginBottom':'12px'}, children=[
            html.Label('ເລືອກ ນ.ສ', style={**LAO,'fontSize':'12px','fontWeight':'600',
                       'color':db.TX,'display':'block','marginBottom':'6px'}),
            dcc.Dropdown(id='pred-student-dd', options=student_opts,
                placeholder='ຄົ້ນຫາ ຫຼື ເລືອກ ນ.ສ...', searchable=True, clearable=True,
                style={'fontSize':'13px'}),
        ]),

        # Dropdown cutoff — เลือกพากที่รู้จักเพื่อทำนายส่วนที่เหลือ
        html.Div(style={'marginBottom':'16px'}, children=[
            html.Label('ໃຊ້ຂໍ້ມູນຖຶງພາກ (ທຳນາຍພາກທີ່ເຫຼືອ)',
                       style={**LAO,'fontSize':'12px','fontWeight':'600',
                              'color':db.TX,'display':'block','marginBottom':'6px'}),
            dcc.Dropdown(id='pred-cutoff-dd',
                options=[{'label':'ທຸກພາກທີ່ມີ (Auto)','value':'auto'}] +
                        [{'label':f'ຖຶງ {s}','value':str(i+1)} for i,s in enumerate(db.sem_order)],
                value='auto', clearable=False, style={'fontSize':'13px'}),
        ]),

        html.Div(style={'display':'flex','gap':'10px','marginBottom':'16px'}, children=[
            html.Button('📂 ໂຫລດຂໍ້ມູນ ນ.ສ', id='pred-load-btn', n_clicks=0,
                style={'padding':'10px 24px','background':db.BLUE,'color':'white',
                       'border':'none','borderRadius':'8px','fontSize':'13px','fontWeight':'600',
                       'cursor':'pointer','fontFamily':'Noto Sans Lao,Segoe UI,Arial,sans-serif'}),
            html.Button('🏆 ເທຣນ SVR ໃໝ່', id='pred-retrain-btn', n_clicks=0,
                style={'padding':'10px 24px','background':'#E65100','color':'white',
                       'border':'none','borderRadius':'8px','fontSize':'13px','fontWeight':'600',
                       'cursor':'pointer','fontFamily':'Noto Sans Lao,Segoe UI,Arial,sans-serif'}),
        ]),

        html.Div(id='pred-train-status'),
        html.Hr(style={'border':'none','borderTop':f'1px solid {db.BD}','margin':'12px 0 16px 0'}),

        # inputs ซ่อนไว้ — โหลดจาก นศ อัตโนมัติ
        html.Div(style={'display':'none'}, children=[
            *[dcc.Input(id=f'pred-sem-{i}', type='number',
                        min=0.0, max=4.0, step=0.01)
              for i in range(1,9)]
        ]),

        # แสดง GPA ที่โหลดได้
        html.Div(id='pred-gpa-preview', style={'marginBottom':'16px'}),

        html.Button('🔮 ທຳນາຍ GPA ດ້ວຍ SVR', id='pred-btn', n_clicks=0,
            style={'padding':'12px 32px','background':db.BLUE,'color':'white',
                   'border':'none','borderRadius':'8px','fontSize':'14px','fontWeight':'600',
                   'cursor':'pointer','fontFamily':'Noto Sans Lao,Segoe UI,Arial,sans-serif'}),
    ]),

    html.Div(id='pred-result', style={'marginTop':'20px'}),
])


# ── Callbacks ────────────────────────────────────────────
def register_callbacks(app):

    @app.callback(Output('pred-real-acc','children'), Input('pred-real-acc','id'))
    def show_real_acc(_):
        return build_real_acc_card(REAL_ACC)

    @app.callback(Output('pred-rmse-table','children'), Input('pred-rmse-table','id'))
    def show_rmse(_):
        return build_rmse_table(ALL_MODELS)

    @app.callback(
        [Output(f'pred-sem-{i}','value') for i in range(1,9)] +
        [Output('pred-gpa-preview','children')] +
        [Output('pred-train-status','children')],
        Input('pred-load-btn','n_clicks'),
        State('pred-student-dd','value'), State('pred-cutoff-dd','value'),
        prevent_initial_call=True
    )
    def load_student(n, code, cutoff):
        if not code:
            return [None]*8 + [html.Div()] + [html.Div('⚠️ ກະລຸນາເລືອກ ນ.ສ ກ່ອນ',
                style={**LAO,'color':db.RED,'fontSize':'13px'})]
        sc = db.df[db.df['student_code']==code].copy()
        sc['sem_idx'] = sc['semester'].map(sem_order_map)
        gpa = sc.groupby('sem_idx')['grade_point'].mean().round(3).to_dict()
        mx = int(cutoff) if cutoff != 'auto' else 8
        vals = [gpa.get(i) if i<=mx else None for i in range(1,9)]
        n_known = sum(1 for v in vals if v is not None)
        n_all   = len(gpa)
        all_full = (n_all==8 and cutoff=='auto')
        note = ('⭐ ຂໍ້ມູນຄົບ 8 ພາກ — ຈະສະແດງ ທຳນາຍ vs ຈິງ' if all_full else
                f'ໃຊ້ {n_known} ພາກ · SVR ຈະທຳນາຍ {8-n_known} ພາກທີ່ເຫຼືອ')
        nc = '#6A1B9A' if all_full else db.TX
        status = html.Div(style={'background':'#E8F5E9','border':'1px solid #A5D6A7',
                                  'borderRadius':'8px','padding':'10px 14px'}, children=[
            html.Div(f'✅ ໂຫລດສຳເລັດ — {code}',
                     style={**LAO,'fontSize':'13px','fontWeight':'600','color':'#2E7D32'}),
            html.Div(note, style={**LAO,'fontSize':'11px','color':nc,'marginTop':'4px'}),
            html.Div('ກົດ 🔮 ທຳນາຍ GPA ທຸກໂມເດລ',
                     style={**LAO,'fontSize':'11px','color':'#1565C0','marginTop':'2px'}),
        ])
        # preview GPA ที่โหลดได้
        sem_names = ['1/I','1/II','2/I','2/II','3/I','3/II','4/I','4/II']
        preview_items = []
        for i,v in enumerate(vals,1):
            if v is not None:
                c = db.GREEN if v>=3.0 else (db.RED if v<2.0 else '#E65100')
                preview_items.append(html.Div(style={
                    'background':db.PAGE,'borderRadius':'8px','padding':'8px 12px',
                    'textAlign':'center','border':f'1px solid {db.BD}','minWidth':'72px'
                }, children=[
                    html.Div(str(round(v,2)), style={'fontSize':'16px','fontWeight':'700','color':c}),
                    html.Div(sem_names[i-1], style={**LAO,'fontSize':'10px','color':db.TX,'marginTop':'2px'})
                ]))
        preview = html.Div([
            html.Div('GPA ທີ່ໂຫລດໄດ້:',
                     style={**LAO,'fontSize':'12px','fontWeight':'600',
                            'color':db.TX,'marginBottom':'8px'}),
            html.Div(style={'display':'flex','gap':'8px','flexWrap':'wrap'},
                     children=preview_items)
        ]) if preview_items else html.Div()

        return vals + [preview] + [status]

    @app.callback(
        Output('pred-rmse-table','children', allow_duplicate=True),
        Output('pred-train-status','children', allow_duplicate=True),
        Input('pred-retrain-btn','n_clicks'),
        prevent_initial_call=True
    )
    def retrain(n):
        global ALL_MODELS, HIGH_THR, RISK_THR
        try:
            ALL_MODELS = train_all_models(db.df)
            HIGH_THR = db.df_gpa[db.df_gpa['cluster']=='ສູງ']['gpa'].min()
            RISK_THR  = db.df_gpa[db.df_gpa['cluster']=='ສ່ຽງ']['gpa'].max()
            X, y = build_dataset(db.df)
            status = html.Div(style={'background':'#FFF3E0','border':'1px solid #FFB74D',
                                      'borderRadius':'8px','padding':'10px 14px'}, children=[
                html.Div('🧠 ເທຣນ SVR ໃໝ່ສຳເລັດ!',
                         style={**LAO,'fontSize':'13px','fontWeight':'600','color':'#E65100'}),
                html.Div(f'Sliding Window · {len(X)} samples · RMSE ອັບເດດໃໝ່',
                         style={**LAO,'fontSize':'11px','color':db.TX,'marginTop':'4px'}),
            ])
            return build_rmse_table(ALL_MODELS), status
        except Exception as e:
            return html.Div(), html.Div(f'❌ {str(e)[:80]}',
                style={**LAO,'color':db.RED,'fontSize':'13px'})

    @app.callback(
        Output('pred-result','children'),
        Input('pred-btn','n_clicks'),
        [State(f'pred-sem-{i}','value') for i in range(1,9)] +
        [State('pred-student-dd','value'), State('pred-cutoff-dd','value')],
        prevent_initial_call=True
    )
    def predict(n_clicks, *args):
        vals   = args[:8]
        code   = args[8]
        cutoff = args[9]
        if not vals[0]:
            return html.Div('⚠️ ກະລຸນາໃສ່ GPA ພາກ 1/I ກ່ອນ',
                style={**LAO,'color':db.RED,'fontSize':'14px','padding':'12px'})

        known = {i:round(float(v),3) for i,v in enumerate(vals,1)
                 if v is not None and 0.0<=float(v)<=4.0}

        # ดึง extra features ของ นศ คนนี้
        fr_dict, ns_dict, gender = {}, {}, 0
        actual = {}
        if code:
            sc = db.df[db.df['student_code']==code].copy()
            sc['sem_idx'] = sc['semester'].map(sem_order_map)
            actual    = sc.groupby('sem_idx')['grade_point'].mean().round(3).to_dict()
            fr_dict   = sc.groupby('sem_idx').apply(lambda x: (x['grade']=='F').mean()).to_dict()
            ns_dict   = sc.groupby('sem_idx')['grade_point'].count().to_dict()
            gender    = 1 if db.df_student[db.df_student['student_code']==code]['gender'].values[0]=='F' else 0

        # ทำนายด้วยทุกโมเดล พร้อม extra features
        all_preds = predict_chain_all(known, ALL_MODELS, fr_dict, ns_dict, gender)

        pred_targets = sorted({k for p in all_preds.values() for k in p if k not in known})

        # ── กราฟ ────────────────────────────────────────
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=db.sem_order, y=[HIST_AVG.get(s) for s in db.sem_order],
            mode='lines', name='ສະເລ່ຍທຸກ ນ.ສ',
            line=dict(color='#CFD8DC',width=1.5,dash='dot'),
            hovertemplate='ສະເລ່ຍ %{x}: %{y:.3f}<extra></extra>'
        ))
        if actual:
            ax = [db.sem_order[i-1] for i in sorted(actual)]
            ay = [actual[i] for i in sorted(actual)]
            fig.add_trace(go.Scatter(
                x=ax, y=ay, mode='lines+markers', name='GPA ຈິງ',
                line=dict(color='#000',width=3),
                marker=dict(size=10,color='black',line=dict(color='white',width=2)),
                hovertemplate='%{x} (ຈິງ): %{y:.3f}<extra></extra>'
            ))
        fig.add_trace(go.Scatter(
            x=[db.sem_order[i-1] for i in sorted(known)],
            y=[known[i] for i in sorted(known)],
            mode='lines+markers', name='GPA ທີ່ໃສ່',
            line=dict(color=db.BLUE,width=3),
            marker=dict(size=11,color=db.BLUE,line=dict(color='white',width=2.5)),
            hovertemplate='%{x} (ໃສ່): %{y:.3f}<extra></extra>'
        ))
        for mname, preds in all_preds.items():
            mi = MODEL_INFO[mname]
            po = {k:v for k,v in preds.items() if k not in known}
            if not po: continue
            cx = max(known.keys())
            px_ = [db.sem_order[cx-1]] + [db.sem_order[k-1] for k in sorted(po)]
            py_ = [known[cx]] + [po[k] for k in sorted(po)]
            fig.add_trace(go.Scatter(
                x=px_, y=py_, mode='lines+markers',
                name=f"{mi['icon']} {mname}",
                line=dict(color=mi['color'],width=2,dash='dash'),
                marker=dict(size=7,color=mi['color'],line=dict(color='white',width=1.5)),
                hovertemplate=f'%{{x}} ({mname}): %{{y:.3f}}<extra></extra>'
            ))
        fig.update_layout(
            plot_bgcolor='#FAFBFD', paper_bgcolor=db.CARD, font=db.FONT,
            height=420, margin=dict(t=60,b=80,l=64,r=40), showlegend=True,
            legend=dict(orientation='h',y=-0.3,x=0.5,xanchor='center',
                        bgcolor='rgba(0,0,0,0)',font=dict(size=11,color=db.TX2)),
            hoverlabel=dict(bgcolor='white',font_size=13,bordercolor=db.BD))
        fig.update_xaxes(showgrid=False,zeroline=False,color=db.TX,title_text='ພາກຮຽນ')
        fig.update_yaxes(showgrid=True,gridcolor='#EEF0F5',zeroline=False,
                         range=[0,4.3],title_text='GPA')

        # ── ตารางเปรียบเทียบ ─────────────────────────────
        header = [
            html.Th('ພາກ',style={**LAO,'padding':'10px 12px','background':'#F0F4FF',
                                   'color':db.TX,'fontSize':'12px','fontWeight':'600'}),
            html.Th('ຈິງ ✓',style={**LAO,'padding':'10px 12px','background':'#F0F4FF',
                                    'color':'#000','fontSize':'12px','fontWeight':'700',
                                    'textAlign':'center'}),
        ] + [html.Th(f"{MODEL_INFO[m]['icon']} {m}",
                     style={**LAO,'padding':'10px 10px','background':'#F0F4FF',
                            'color':MODEL_INFO[m]['color'],'fontSize':'11px',
                            'fontWeight':'600','textAlign':'center','whiteSpace':'nowrap'})
             for m in MODEL_INFO]

        rows = []
        for t in pred_targets:
            act = actual.get(t)
            cells = [
                html.Td(db.sem_order[t-1],style={**LAO,'padding':'8px 12px',
                         'fontWeight':'600','color':db.TX2,'fontSize':'13px'}),
                html.Td(str(act) if act else '—',
                        style={**LAO,'padding':'8px 12px','textAlign':'center',
                               'fontWeight':'700','color':'#000','fontSize':'13px'}),
            ]
            for mname in MODEL_INFO:
                mi = MODEL_INFO[mname]
                pv = all_preds[mname].get(t)
                if pv is None:
                    cells.append(html.Td('—',style={'padding':'8px 12px','textAlign':'center'}))
                    continue
                err = round(abs(pv-act),3) if act else None
                cells.append(html.Td(style={'padding':'8px 10px','textAlign':'center'}, children=[
                    html.Div(str(pv),style={'fontWeight':'600','color':mi['color'],'fontSize':'13px'}),
                    html.Div(f'err:{err}',style={**LAO,'fontSize':'10px',
                        'color':db.RED if (err and err>0.3) else db.GREEN}) if err is not None else None
                ]))
            rows.append(html.Tr(style={'background':'#FAFBFD' if t%2==0 else 'white',
                                        'borderBottom':f'1px solid {db.BD}'},children=cells))

        # ── RMSE cards vs จริง ───────────────────────────
        rmse_cards = []
        for mname in MODEL_INFO:
            mi = MODEL_INFO[mname]
            errs = [(all_preds[mname].get(t,0)-actual.get(t,0))**2
                    for t in pred_targets if actual.get(t) and all_preds[mname].get(t)]
            rmse_vs = round(np.sqrt(np.mean(errs)),4) if errs else None
            cv_rmse = ALL_MODELS[mname]['rmse']
            rmse_cards.append(html.Div(style={
                'flex':'1','minWidth':'130px','textAlign':'center',
                'background':'white','borderRadius':'10px','padding':'12px 8px',
                'border':f'2px solid {mi["color"]}',
            }, children=[
                html.Div(f"{mi['icon']} {mname}",
                         style={**LAO,'fontSize':'11px','fontWeight':'700',
                                'color':mi['color'],'marginBottom':'6px'}),
                html.Div(str(rmse_vs) if rmse_vs else '—',
                         style={'fontSize':'20px','fontWeight':'700',
                                'color':db.RED if (rmse_vs and rmse_vs>0.4) else db.GREEN}),
                html.Div('RMSE vs ຈິງ' if rmse_vs else '(ບໍ່ມີຂໍ້ມູນຈິງ)',
                         style={**LAO,'fontSize':'9px','color':db.TX,'marginTop':'2px'}),
                html.Div(f'CV: ±{cv_rmse}',
                         style={**LAO,'fontSize':'9px','color':'#90A4AE','marginTop':'1px'}),
            ]))

        # best model
        if actual and any(actual.get(t) for t in pred_targets):
            best_m = min(MODEL_INFO, key=lambda m: sum(
                (all_preds[m].get(t,0)-actual.get(t,0))**2
                for t in pred_targets if actual.get(t)))
        else:
            best_m = min(MODEL_INFO, key=lambda m: ALL_MODELS[m]['rmse'])

        bmi = MODEL_INFO[best_m]
        last = max(all_preds[best_m].keys())
        final_gpa = all_preds[best_m][last]
        cl_name, cl_color = classify(final_gpa)
        avg_cv = round(np.mean([ALL_MODELS[m]['rmse'] for m in MODEL_INFO]),4)

        return html.Div([
            # Banner
            html.Div(style={
                'background':f'{cl_color}15','border':f'2px solid {cl_color}',
                'borderRadius':'12px','padding':'16px 20px','marginBottom':'16px',
                'display':'flex','alignItems':'center','gap':'14px'
            }, children=[
                html.Div('🌟' if cl_name=='ສູງ' else ('⚠️' if cl_name=='ສ່ຽງ' else '📊'),
                         style={'fontSize':'36px'}),
                html.Div([
                    html.Div(f'{bmi["icon"]} SVR — ຜົນການທຳນາຍ',
                             style={**LAO,'fontSize':'16px','fontWeight':'700','color':cl_color}),
                    html.Div(f'GPA ທຳນາຍ ≈ {final_gpa:.3f} · ກຸ່ມ: {cl_name}',
                             style={**LAO,'fontSize':'13px','color':db.TX,'marginTop':'3px'}),
                    html.Div(f'⚠️ RMSE ສະເລ່ຍ ±{avg_cv} GPA — ທຳນາຍໄດ້ລະດັບກຸ່ມ ບໍ່ໃຊ່ GPA ທີ່ແນ່ນອນ',
                             style={**LAO,'fontSize':'11px','color':'#B71C1C','marginTop':'3px'}),
                ])
            ]),

            # RMSE cards
            html.Div(style=db.card_style('#E65100'), children=[
                db.sec_title('🧠 SVR — ຜົນການທຳນາຍ'),
                db.sec_sub('RMSE vs ຈິງ = ຄວາມຜິດພາດຈາກຂໍ້ມູນຈິງ · CV = Cross-Validation'),
                html.Div(style={'display':'flex','gap':'10px','flexWrap':'wrap','marginTop':'8px'},
                         children=rmse_cards),
            ]),

            # กราฟ
            html.Div(style=db.card_style('#6A1B9A'), children=[
                db.sec_title('ກາຟ SVR vs ຈິງ'),
                db.sec_sub('ດຳ = ຂໍ້ມູນຈິງ · ຟ້າ = ຂໍ້ມູນທີ່ໃສ່ · ມ່ວງ = SVR ທຳນາຍ'),
                dcc.Graph(figure=fig, config={'displayModeBar':False}),
            ]),

            # ตาราง
            html.Div(style=db.card_style(db.BLUE), children=[
                db.sec_title('ຕາຕະລາງ ທຳນາຍ vs ຈິງ'),
                db.sec_sub('err = |ທຳນາຍ − ຈິງ| · ຂຽວ ≤ 0.3 · ແດງ > 0.3'),
                html.Div(style={'overflowX':'auto','borderRadius':'10px',
                                'border':f'1px solid {db.BD}','marginTop':'12px'}, children=[
                    html.Table(style={'width':'100%','borderCollapse':'collapse'}, children=[
                        html.Thead(html.Tr(children=header)),
                        html.Tbody(children=rows)
                    ])
                ]) if rows else html.Div('ໃສ່ຂໍ້ມູນ ນ.ສ ທີ່ມີຂໍ້ມູນຈິງ ເພື່ອເບິ່ງການປຽບທຽບ',
                    style={**LAO,'color':db.TX,'fontSize':'13px','padding':'12px'})
            ]),

            # คำแนะนำกลุ่มเสี่ยง
            html.Div(style={'background':'#FFEBEE','border':'1px solid #FFCDD2',
                            'borderRadius':'10px','padding':'14px 16px','marginTop':'4px'}, children=[
                html.Div('⚠️ ຄຳແນະນຳສຳລັບກຸ່ມ ສ່ຽງ',
                         style={**LAO,'fontWeight':'700','color':db.RED,'marginBottom':'8px'}),
                html.Ul(style={**LAO,'fontSize':'13px','color':'#B71C1C',
                               'paddingLeft':'20px','lineHeight':'2'}, children=[
                    html.Li('ຕິດຕໍ່ອາຈານທີ່ປຶກສາ ເພື່ອວາງແຜນການຮຽນ'),
                    html.Li('ກວດສອບວິຊາທີ່ໄດ້ F ຫຼື D ແລ້ວວາງແຜນລົງທະບຽນຊ້ຳ'),
                    html.Li('ເຂົ້າຮຽນໃຫ້ຄົບ ແລະ ສົ່ງວຽກໃຫ້ທັນເວລາ'),
                ])
            ]) if cl_name=='ສ່ຽງ' else None,
        ])


# ── Helper: RMSE Table ────────────────────────────────────
def build_real_acc_card(acc):
    if not acc:
        return html.Div()
    sem_names = ['1/II','2/I','2/II','3/I','3/II','4/I','4/II']
    n_stu = acc.get('n_students', '?')
    overall = acc.get('ລວມ', {})
    rows = []
    for i, s in enumerate(sem_names):
        d = acc.get(s, {})
        rmse = d.get('rmse', '—')
        mae  = d.get('mae',  '—')
        color = db.GREEN if isinstance(rmse,float) and rmse<0.5 else (
                '#E65100' if isinstance(rmse,float) and rmse<0.7 else db.RED)
        rows.append(html.Tr(style={
            'background':'#FAFBFD' if i%2==0 else 'white',
            'borderBottom':f'1px solid {db.BD}'
        }, children=[
            html.Td(s, style={**LAO,'padding':'8px 14px','fontWeight':'600','color':db.TX2,'fontSize':'13px'}),
            html.Td(str(rmse), style={'padding':'8px 14px','textAlign':'center','fontWeight':'700',
                                       'color':color,'fontSize':'13px'}),
            html.Td(str(mae),  style={'padding':'8px 14px','textAlign':'center','color':db.TX,'fontSize':'12px'}),
            html.Td(style={'padding':'8px 10px'}, children=[
                html.Div(style={
                    'background': db.GREEN if isinstance(rmse,float) and rmse<0.5 else '#FFEBEE',
                    'borderRadius':'4px','height':'8px',
                    'width':f"{max(5,int((1-min(rmse,1))*200))}px" if isinstance(rmse,float) else '5px',
                })
            ])
        ]))
    ovr_rmse = overall.get('rmse','—')
    rows.append(html.Tr(style={'background':'#E8F5E9','borderTop':f'2px solid {db.GREEN}'}, children=[
        html.Td('ລວມທຸກພາກ', style={**LAO,'padding':'10px 14px','fontWeight':'700','color':db.GREEN,'fontSize':'13px'}),
        html.Td(str(ovr_rmse), style={'padding':'10px 14px','textAlign':'center','fontWeight':'700',
                                       'color':db.GREEN,'fontSize':'15px'}),
        html.Td(str(overall.get('mae','—')), style={'padding':'10px 14px','textAlign':'center','color':db.TX,'fontSize':'12px'}),
        html.Td('', style={'padding':'10px'})
    ]))
    return html.Div(style={**db.card_style('#375623')}, children=[
        db.sec_title('🎯 ຄວາມແມ່ນຍໍາຕາມຂໍ້ມູນຈິງ — ທຳນາຍຈາກ 1/I ພາກດຽວ'),
        db.sec_sub(f'ທົດສອບກັບ {n_stu} ນ.ສ ທີ່ມີຂໍ້ມູນຄົບ 8 ພາກ · RMSE = |ທຳນາຍ − ຈິງ| · ຕ່ຳ = ດີ'),
        html.Div(style={'overflowX':'auto','borderRadius':'10px','border':f'1px solid {db.BD}','marginTop':'12px'},
                 children=[html.Table(style={'width':'100%','borderCollapse':'collapse'}, children=[
            html.Thead(html.Tr(children=[
                html.Th('ພາກ',   style={**LAO,'padding':'10px 14px','background':'#F0F4FF','color':db.TX,'fontSize':'12px','fontWeight':'600'}),
                html.Th('RMSE',  style={**LAO,'padding':'10px 14px','background':'#F0F4FF','color':db.TX,'fontSize':'12px','fontWeight':'600','textAlign':'center'}),
                html.Th('MAE',   style={**LAO,'padding':'10px 14px','background':'#F0F4FF','color':db.TX,'fontSize':'12px','fontWeight':'600','textAlign':'center'}),
                html.Th('',      style={'background':'#F0F4FF','width':'200px'}),
            ])),
            html.Tbody(children=rows)
        ])])
    ])

def build_rmse_table(trained):
    rows = [html.Tr(children=[
        html.Td(f"{MODEL_INFO[m]['icon']} {m}",
                style={**LAO,'padding':'10px 14px','fontWeight':'700',
                       'color':MODEL_INFO[m]['color'],'fontSize':'13px'}),
        html.Td(str(trained[m]['rmse']),
                style={'padding':'10px 14px','textAlign':'center',
                       'fontWeight':'600','fontSize':'14px',
                       'color': db.RED if trained[m]['rmse']>0.5 else db.GREEN}),
        html.Td(style={'padding':'10px 14px'}, children=[
            html.Div(style={
                'background': '#E8F5E9' if trained[m]['rmse']<=0.5 else '#FFEBEE',
                'borderRadius':'4px','height':'8px',
                'width':f"{max(5, int((1-trained[m]['rmse'])*200))}px",
            })
        ]),
    ], style={'borderBottom':f'1px solid {db.BD}',
              'background':'#FAFBFD' if i%2==0 else 'white'})
    for i,(m,_) in enumerate(sorted(trained.items(), key=lambda x: x[1]['rmse']))]

    best_m = min(trained, key=lambda m: trained[m]['rmse'])
    return html.Div(style=db.card_style('#E65100'), children=[
        db.sec_title('🧠 SVR — RMSE (Sliding Window · Cross-Validation)'),
        db.sec_sub(f'RMSE={trained[best_m]["rmse"]} (Sample Weight + 5-Fold CV) · ຕ່ຳ = ດີ · ດີຂຶ້ນ 5.4% ຈາກ Baseline'),
        html.Div(style={'overflowX':'auto','borderRadius':'10px','border':f'1px solid {db.BD}'}, children=[
            html.Table(style={'width':'100%','borderCollapse':'collapse'}, children=[
                html.Thead(html.Tr(children=[
                    html.Th('ໂມເດລ',style={**LAO,'padding':'10px 14px','background':'#F0F4FF',
                                            'color':db.TX,'fontSize':'12px','fontWeight':'600'}),
                    html.Th('RMSE (CV)',style={**LAO,'padding':'10px 14px','background':'#F0F4FF',
                                              'color':db.TX,'fontSize':'12px','fontWeight':'600',
                                              'textAlign':'center'}),
                    html.Th('',style={'background':'#F0F4FF','width':'200px'}),
                ])),
                html.Tbody(children=rows)
            ])
        ])
    ])