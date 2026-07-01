from dash import html, dcc, Input, Output, State, no_update
from flask import session as flask_session
import plotly.graph_objects as go
import numpy as np
import warnings
warnings.filterwarnings('ignore')
import db

from ml.predictor import get_or_train_predictor

LAO = {'fontFamily': 'Noto Sans Lao,Segoe UI,Arial,sans-serif'}
sem_order_map = {s: i + 1 for i, s in enumerate(db.sem_order)}

MODEL_INFO = {
    'RandomForest': {'color': '#2E7D32', 'icon': '🌲'},
    'XGBoost': {'color': '#E65100', 'icon': '⚡'},
}

PREDICTOR = get_or_train_predictor(db.df, db.df_student, db.sem_order)
ALL_MODELS = PREDICTOR.metrics if PREDICTOR.is_ready else {}
REAL_ACC = PREDICTOR.evaluate_real_scenario(db.df, db.df_student, db.sem_order) if PREDICTOR.is_ready else {}

HIGH_THR = db.df_gpa[db.df_gpa['cluster'] == 'ສູງ']['gpa'].min() if len(db.df_gpa) > 0 and 'cluster' in db.df_gpa.columns else 3.5
RISK_THR = db.df_gpa[db.df_gpa['cluster'] == 'ສ່ຽງ']['gpa'].max() if len(db.df_gpa) > 0 and 'cluster' in db.df_gpa.columns else 2.0


DROP_THRESHOLD = 0.8   # ลดลงมากกว่านี้ใน 1 เทอม = "หล่นแรง"
NEAR_ZERO = 0.5         # GPA ต่ำกว่านี้ = แทบจะตกทุกวิชา


def analyze_trend(actual):
    """
    ตรวจ pattern จาก GPA จริงที่มีอยู่ (ไม่ใช่ค่าทำนาย):
    - หล่นแรงระหว่าง 2 เทอมติดกัน (เกิน DROP_THRESHOLD)
    - มีเทอมที่ GPA ใกล้ 0 (แทบตกทุกวิชา)
    คืนค่า dict {severity, title, detail, actions} หรือ None ถ้าไม่พบความเสี่ยง
    """
    sem_names = {i: db.sem_order[i - 1] for i in range(1, 9)}
    known = sorted(actual.items())
    if len(known) < 2:
        return None

    # หาช่วงที่หล่นแรงที่สุด
    biggest_drop = None
    for (i1, g1), (i2, g2) in zip(known, known[1:]):
        if i2 - i1 != 1:
            continue
        drop = g1 - g2
        if biggest_drop is None or drop > biggest_drop[2]:
            biggest_drop = (i1, i2, drop)

    zero_sems = [i for i, g in known if g <= NEAR_ZERO]

    if zero_sems:
        worst = zero_sems[0]
        return {
            'severity': 'critical',
            'mark_sem_idx': worst,
            'mark_icon': '🆘',
            'title': f'🆘 ພົບ GPA ໃກ້ 0 ທີ່ພາກ {sem_names[worst]} ({actual[worst]:.2f})',
            'detail': 'ແທບຕົກທຸກວິຊາໃນພາກນັ້ນ — ອາດແມ່ນຢຸດເຂົ້າຮຽນ, ມີປັນຫາສ່ວນຕົວ, ຫຼື W/ຖອນຮຽນກາງທາງ',
            'actions': [
                'ຕິດຕໍ່ນັກສຶກສາ/ຜູ້ປົກຄອງ ໂດຍກົງເພື່ອສອບຖາມສາເຫດ',
                'ກວດສອບສະຖານະການລົງທະບຽນ — ຍັງເປັນນັກສຶກສາປະຈຳຢູ່ບໍ່',
                'ພິຈາລະນາແຜນ leave of absence ຫຼື ແຜນຟື້ນຟູການຮຽນສະເພາະຄົນ',
            ],
        }

    if biggest_drop and biggest_drop[2] >= DROP_THRESHOLD:
        i1, i2, drop = biggest_drop
        return {
            'severity': 'warning',
            'mark_sem_idx': i2,
            'mark_icon': '⚠️',
            'title': f'📉 GPA ຫຼຸດແຮງ {sem_names[i1]} → {sem_names[i2]}: {actual[i1]:.2f} → {actual[i2]:.2f} (−{drop:.2f})',
            'detail': 'ຫຼຸດລົງໄວກວ່າປົກກະຕິໃນພາກດຽວ — ຄວນຮີບກວດສອບກ່ອນຈະຫຼຸດຕໍ່ໃນພາກໜ້າ',
            'actions': [
                f'ກວດສອບລາຍວິຊາທີ່ໄດ້ເກຣດຕ່ຳໃນພາກ {sem_names[i2]} ວ່າເປັນວິຊາໃດ',
                'ນັດອາຈານທີ່ປຶກສາ ກ່ອນເລີ່ມພາກຮຽນຕໍ່ໄປ',
                'ຕິດຕາມຜົນການຮຽນຖີ່ຂຶ້ນ (ທຸກ 2-3 ອາທິດ) ໃນພາກຕໍ່ໄປ',
            ],
        }

    return None


def classify(gpa):
    if gpa >= HIGH_THR:
        return 'ສູງ', db.GREEN
    if gpa <= RISK_THR:
        return 'ສ່ຽງ', db.RED
    return 'ກາງ', db.BLUE


HIST_AVG = {
    sem: round(db.df[db.df['semester'] == sem].groupby('student_code')['grade_point'].mean().mean(), 3)
    if len(db.df) > 0 else 0.0
    for sem in db.sem_order
}

def _student_opts():
    return [
        {'label': f"{r['student_code']} · {'ຊາຍ' if r['gender'] == 'M' else 'ຍິງ'}", 'value': r['student_code']}
        for _, r in db.df_student.sort_values('student_code').iterrows()
    ] if len(db.df_student) > 0 else []


def layout():
    student_opts = _student_opts()
    return html.Div(className='page-wrap', style={'padding': '28px 32px', 'background': db.PAGE, 'minHeight': '100vh'}, children=[

    html.Div(style={'marginBottom': '24px'}, children=[
        html.Div('ຄາດຄະເນ GPA', style={'fontSize': '22px', 'fontWeight': '700', 'color': db.TX2}),
        html.Div('Multi-Output · Random Forest / XGBoost · ເລືອກວ່າຮູ້ຂໍ້ມູນຮອດເທີນໃດ → ຄາດຄະເນພາກທີ່ເຫຼືອ',
                 style={**LAO, 'fontSize': '13px', 'color': db.TX, 'marginTop': '4px'}),
    ]),

    html.Div(style={
        'background': '#FFEBEE', 'borderRadius': '12px', 'padding': '16px 20px',
        'marginBottom': '20px', 'border': '2px solid #EF9A9A',
    }, children=[
        html.Div('🚨 ອ່ານກ່ອນໃຊ້ງານ', style={**LAO, 'fontSize': '15px', 'fontWeight': '700', 'color': '#B71C1C', 'marginBottom': '10px'}),
        html.Div(style={'display': 'flex', 'flexDirection': 'column', 'gap': '6px'}, children=[
            html.Div('⚠️  ລະບົບນີ້ວິເຄາະໄດ້ພຽງແຕ່ກຸ່ມ (ສູງ / ກາງ / ສ່ຽງ) ເທົ່ານັ້ນ',
                     style={**LAO, 'fontSize': '13px', 'fontWeight': '700', 'color': '#C62828'}),
            html.Div('⚠️  ຕົວເລກ GPA ທີ່ສະແດງ ແມ່ນພຽງຄ່າປະມານການ ບໍ່ແມ່ນ GPA ທີ່ແນ່ນອນ',
                     style={**LAO, 'fontSize': '13px', 'fontWeight': '700', 'color': '#C62828'}),
            html.Div('📊  ຍິ່ງປ້ອນ GPA ຫຼາຍພາກ (k) → ຄາດຄະເນພາກທີ່ເຫຼືອໄດ້ແມ່ນຍຳກວ່າ',
                     style={**LAO, 'fontSize': '12px', 'color': '#B71C1C', 'marginTop': '4px'}),
            html.Div('✅  ໃຊ້ເພື່ອສັງເກດແນວໂນ້ມເທົ່ານັ້ນ ຢ່າໃຊ້ຕັດສິນໃຈສຳຄັນ',
                     style={**LAO, 'fontSize': '12px', 'color': '#B71C1C'}),
        ])
    ]),

    html.Div(id='pred-rmse-table', style={'marginBottom': '20px'}),
    html.Div(id='pred-real-acc', style={'marginBottom': '20px'}),

    html.Div(style=db.card_style(db.BLUE), children=[
        db.sec_title('ເລືອກ ນ.ສ ຫຼື ປ້ອນ GPA ດ້ວຍຕົນເອງ'),
        db.sec_sub('ຍິ່ງຮູ້ຂໍ້ມູນຈິງຫຼາຍພາກ ໂມເດລຈະຄາດຄະເນພາກທີ່ເຫຼືອໄດ້ແມ່ນຍຳກວ່າ'),

        html.Div(style={'marginBottom': '12px'}, children=[
            html.Label('ເລືອກ ນ.ສ', style={**LAO, 'fontSize': '12px', 'fontWeight': '600',
                       'color': db.TX, 'display': 'block', 'marginBottom': '6px'}),
            dcc.Dropdown(id='pred-student-dd', options=student_opts,
                         placeholder='ຄົ້ນຫາ ຫຼື ເລືອກ ນ.ສ...', searchable=True, clearable=True,
                         persistence=True, persistence_type='memory',
                         style={'fontSize': '13px'}),
        ]),

        html.Div(className='pred-btn-row', style={'display': 'flex', 'gap': '10px', 'marginBottom': '16px'}, children=[
            html.Button('🔍 ວິເຄາະ ນ.ສ ຄົນນີ້', id='pred-load-btn', n_clicks=0,
                        style={'padding': '10px 24px', 'background': db.BLUE, 'color': 'white',
                               'border': 'none', 'borderRadius': '8px', 'fontSize': '13px', 'fontWeight': '600',
                               'cursor': 'pointer', 'fontFamily': 'Noto Sans Lao,Segoe UI,Arial,sans-serif'}),
            html.Div(id='pred-retrain-wrap', style={'display': 'none'}, children=[
                html.Button('🏆 ເທຣນໂມເດລໃໝ່ທັງໝົດ', id='pred-retrain-btn', n_clicks=0,
                            style={'padding': '10px 24px', 'background': '#E65100', 'color': 'white',
                                   'border': 'none', 'borderRadius': '8px', 'fontSize': '13px', 'fontWeight': '600',
                                   'cursor': 'pointer', 'fontFamily': 'Noto Sans Lao,Segoe UI,Arial,sans-serif'}),
            ]),
        ]),

        dcc.Loading(
            id='pred-train-loading',
            custom_spinner=html.Div(className='cs-spinner-backdrop', children=[
                html.Div(className='cs-spinner-wrap', children=[
                    html.Div(className='cs-spinner-ring'),
                    html.Div('ກຳລັງເທຣນໂມເດລ...', className='cs-spinner-text'),
                ]),
            ]),
            children=html.Div(id='pred-train-status'),
        ),
        html.Hr(style={'border': 'none', 'borderTop': f'1px solid {db.BD}', 'margin': '12px 0 16px 0'}),

        html.Div(style={'marginBottom': '16px'}, children=[
            html.Label('ຮູ້ຂໍ້ມູນຮອດເທີນໃດ? (k)', style={**LAO, 'fontSize': '12px', 'fontWeight': '600',
                       'color': db.TX, 'display': 'block', 'marginBottom': '6px'}),
            dcc.Dropdown(id='pred-known-k',
                         options=[{'label': f'ຮູ້ {k} ພາກ ({db.sem_order[0]} → {db.sem_order[k-1]})', 'value': k}
                                  for k in range(1, 8)],
                         value=1, clearable=False,
                         persistence=True, persistence_type='memory',
                         className='pred-k-drop', style={'fontSize': '13px', 'maxWidth': '320px'}),
        ]),

        html.Div(className='pred-gpa-grid', style={'display': 'flex', 'gap': '12px', 'flexWrap': 'wrap', 'marginBottom': '16px'}, children=[
            html.Div(id=f'pred-sem-{i}-wrap', style={'display': 'none' if i > 1 else 'block'}, children=[
                html.Label(f'GPA {db.sem_order[i-1]}', style={**LAO, 'fontSize': '11px', 'fontWeight': '600',
                           'color': db.TX, 'display': 'block', 'marginBottom': '4px'}),
                dcc.Input(id=f'pred-sem-{i}', type='number', min=0.0, max=4.0, step=0.01,
                          persistence=True, persistence_type='memory',
                          style={'width': '100px', 'padding': '8px 12px', 'fontSize': '14px',
                                 'borderRadius': '8px', 'border': f'1px solid {db.BD}'}),
            ]) for i in range(1, 8)
        ]),

        html.Div(id='pred-gpa-preview', style={'marginBottom': '16px'}),

        html.Div('🔮 ຜົນຄາດຄະເນຈະອັບເດດອັດຕະໂນມັດທັນທີທີ່ປ້ອນ GPA ຄົບ',
                 style={**LAO, 'fontSize': '12px', 'color': '#90A4AE', 'fontStyle': 'italic'}),
    ]),

    html.Div(id='pred-result', style={'marginTop': '20px'}),
])


def register_callbacks(app):

    @app.callback(Output('pred-real-acc', 'children'), Input('pred-real-acc', 'id'))
    def show_real_acc(_):
        return build_real_acc_card(REAL_ACC)

    @app.callback(Output('pred-retrain-wrap', 'style'), Input('pred-retrain-wrap', 'id'))
    def show_retrain_btn(_):
        is_admin = flask_session.get('role') == 'admin'
        return {'display': 'block'} if is_admin else {'display': 'none'}

    @app.callback(Output('pred-rmse-table', 'children'), Input('pred-rmse-table', 'id'))
    def show_rmse(_):
        return build_rmse_table(ALL_MODELS)

    @app.callback(
        [Output(f'pred-sem-{i}-wrap', 'style') for i in range(1, 8)],
        Input('pred-known-k', 'value'),
    )
    def toggle_sem_inputs(k):
        k = k or 1
        return [{'display': 'block'} if i <= k else {'display': 'none'} for i in range(1, 8)]

    @app.callback(
        [Output(f'pred-sem-{i}', 'value') for i in range(1, 8)] +
        [Output('pred-known-k', 'value', allow_duplicate=True)] +
        [Output('pred-gpa-preview', 'children')] +
        [Output('pred-train-status', 'children')],
        Input('pred-load-btn', 'n_clicks'),
        State('pred-student-dd', 'value'),
        prevent_initial_call=True
    )
    def load_student(n, code):
        if not code:
            return [None] * 7 + [1] + [html.Div()] + [html.Div('⚠️ ກະລຸນາເລືອກ ນ.ສ ກ່ອນ',
                style={**LAO, 'color': db.RED, 'fontSize': '13px'})]

        sc = db.df[db.df['student_code'] == code].copy()
        sc['sem_idx'] = sc['semester'].map(sem_order_map)
        gpa = sc.groupby('sem_idx')['grade_point'].mean().round(3).to_dict()
        sem_vals = [gpa.get(i) for i in range(1, 8)]
        n_all = len(gpa)
        # k = จำนวนเทอมที่มีข้อมูลจริงต่อเนื่องตั้งแต่เทอม 1 (สูงสุด 7)
        k = 0
        for v in sem_vals:
            if v is None:
                break
            k += 1
        k = max(k, 1)

        note = ('⭐ ຂໍ້ມູນຄົບ 8 ພາກ — ຈະສະແດງ GPA ຕົວຈິງ VS GPA ຄາດຄະເນ' if n_all == 8 else
                f'ມີຂໍ້ມູນຈິງ {k} ພາກ · ຄາດຄະເນພາກທີ່ເຫຼືອ')
        status = html.Div(style={'background': '#E8F5E9', 'border': '1px solid #A5D6A7',
                                  'borderRadius': '8px', 'padding': '10px 14px'}, children=[
            html.Div(f'✅ ໂຫລດສຳເລັດ — {code}',
                     style={**LAO, 'fontSize': '13px', 'fontWeight': '600', 'color': '#2E7D32'}),
            html.Div(note, style={**LAO, 'fontSize': '11px', 'color': db.TX, 'marginTop': '4px'}),
        ])

        sem_names = ['1/I', '1/II', '2/I', '2/II', '3/I', '3/II', '4/I', '4/II']
        preview_items = []
        for i, v in enumerate(sem_vals, 1):
            if v is not None:
                c = db.GREEN if v >= 3.0 else (db.RED if v < 2.0 else '#E65100')
                preview_items.append(html.Div(style={
                    'background': db.PAGE, 'borderRadius': '8px', 'padding': '8px 12px',
                    'textAlign': 'center', 'border': f'1px solid {db.BD}', 'minWidth': '72px'
                }, children=[
                    html.Div(str(round(v, 2)), style={'fontSize': '16px', 'fontWeight': '700', 'color': c}),
                    html.Div(sem_names[i - 1], style={**LAO, 'fontSize': '10px', 'color': db.TX, 'marginTop': '2px'})
                ]))
        preview = html.Div([
            html.Div('GPA ທີ່ໂຫລດໄດ້ (ຈິງ):',
                     style={**LAO, 'fontSize': '12px', 'fontWeight': '600', 'color': db.TX, 'marginBottom': '8px'}),
            html.Div(style={'display': 'flex', 'gap': '8px', 'flexWrap': 'wrap'}, children=preview_items)
        ]) if preview_items else html.Div()

        return sem_vals + [k] + [preview] + [status]

    @app.callback(
        Output('pred-rmse-table', 'children', allow_duplicate=True),
        Output('pred-train-status', 'children', allow_duplicate=True),
        Input('pred-retrain-btn', 'n_clicks'),
        prevent_initial_call=True
    )
    def retrain(n):
        global PREDICTOR, ALL_MODELS, REAL_ACC, HIGH_THR, RISK_THR
        if flask_session.get('role') != 'admin':
            return no_update, html.Div('🚫 ສະເພາະ admin ເທົ່ານັ້ນທີ່ເທຣນໂມເດລໃໝ່ໄດ້',
                style={**LAO, 'color': db.RED, 'fontSize': '13px'})
        try:
            PREDICTOR.train_from_df(db.df, db.df_student, db.sem_order, save=True)
            ALL_MODELS = PREDICTOR.metrics
            REAL_ACC = PREDICTOR.evaluate_real_scenario(db.df, db.df_student, db.sem_order)
            HIGH_THR = db.df_gpa[db.df_gpa['cluster'] == 'ສູງ']['gpa'].min()
            RISK_THR = db.df_gpa[db.df_gpa['cluster'] == 'ສ່ຽງ']['gpa'].max()
            status = html.Div(style={'background': '#FFF3E0', 'border': '1px solid #FFB74D',
                                      'borderRadius': '8px', 'padding': '10px 14px'}, children=[
                html.Div('🧠 ເທຣນໂມເດລໃໝ່ສຳເລັດ!',
                         style={**LAO, 'fontSize': '13px', 'fontWeight': '600', 'color': '#E65100'}),
                html.Div('Multi-Output · Random Forest + XGBoost · ບັນທຶກ models/gpa_predictor.pkl',
                         style={**LAO, 'fontSize': '11px', 'color': db.TX, 'marginTop': '4px'}),
            ])
            return build_rmse_table(ALL_MODELS), status
        except Exception as e:
            return html.Div(), html.Div(f'❌ {str(e)[:80]}',
                style={**LAO, 'color': db.RED, 'fontSize': '13px'})

    @app.callback(
        Output('pred-result', 'children'),
        [Input('pred-known-k', 'value')] +
        [Input(f'pred-sem-{i}', 'value') for i in range(1, 8)] +
        [State('pred-student-dd', 'value')],
    )
    def predict(known_k, *args):
        sem_vals = args[:7]
        code = args[7]

        known_k = known_k or 1
        known_gpas = sem_vals[:known_k]

        # ยังไม่มีค่าเลย (เพิ่งเปิดหน้าครั้งแรก ไม่มีข้อมูลที่จำไว้) — ไม่ต้องโชว์คำเตือน
        if all(v is None for v in known_gpas):
            return html.Div()

        if any(v is None for v in known_gpas) or not all(0.0 <= float(v) <= 4.0 for v in known_gpas):
            return html.Div(f'⚠️ ກະລຸນາໃສ່ GPA ໃຫ້ຄົບທຸກພາກທີ່ "ຮູ້ {known_k} ພາກ" (0.00 – 4.00)',
                            style={**LAO, 'color': db.RED, 'fontSize': '14px', 'padding': '12px'})

        if not PREDICTOR.is_ready:
            return html.Div('⚠️ ຍັງບໍ່ມີໂມເດລ — ກົດ "ເທຣນໂມເດລໃໝ່" ກ່ອນ',
                            style={**LAO, 'color': db.RED, 'fontSize': '14px', 'padding': '12px'})

        known_gpas = [round(float(v), 3) for v in known_gpas]
        gpa_1 = known_gpas[0]

        fr_1, ns_1, gender, major = 0.0, 0.0, 0, None
        actual = {}
        if code:
            sc = db.df[db.df['student_code'] == code].copy()
            sc['sem_idx'] = sc['semester'].map(sem_order_map)
            actual = sc.groupby('sem_idx')['grade_point'].mean().round(3).to_dict()
            if 1 in sc['sem_idx'].values:
                s1 = sc[sc['sem_idx'] == 1]
                fr_1 = float((s1['grade'] == 'F').mean())
                ns_1 = float(len(s1))
            stu = db.df_student[db.df_student['student_code'] == code]
            gender = 1 if stu['gender'].values[0] == 'F' else 0
            major = stu['major'].values[0] if 'major' in stu.columns else None

        all_preds = PREDICTOR.predict_from_known(
            known_gpas, gender=gender, fr_1=fr_1, ns_1=ns_1, major=major,
        )
        pred_targets = list(range(known_k + 1, 9))

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=db.sem_order, y=[HIST_AVG.get(s) for s in db.sem_order],
            mode='lines', name='ສະເລ່ຍທຸກ ນ.ສ',
            line=dict(color='#CFD8DC', width=1.5, dash='dot'),
            hovertemplate='ສະເລ່ຍ %{x}: %{y:.3f}<extra></extra>'
        ))
        if actual:
            ax = [db.sem_order[i - 1] for i in sorted(actual)]
            ay = [actual[i] for i in sorted(actual)]
            fig.add_trace(go.Scatter(
                x=ax, y=ay, mode='lines+markers', name='GPA ຕົວຈິງ',
                line=dict(color='#000', width=3),
                marker=dict(size=10, color='black', line=dict(color='white', width=2)),
                hovertemplate='%{x} (ຕົວຈິງ): %{y:.3f}<extra></extra>'
            ))
        fig.add_trace(go.Scatter(
            x=db.sem_order[:known_k], y=known_gpas,
            mode='markers', name=f'GPA ທີ່ໃສ່ ({known_k} ພາກ)',
            marker=dict(size=14, color=db.BLUE, line=dict(color='white', width=2.5)),
            hovertemplate='%{x} (ໃສ່): %{y:.3f}<extra></extra>'
        ))
        for mname, preds in all_preds.items():
            mi = MODEL_INFO.get(mname, {'color': '#666', 'icon': '📈'})
            px_ = [db.sem_order[known_k - 1]] + [db.sem_order[t - 1] for t in pred_targets]
            py_ = [gpa_1 if known_k == 1 else known_gpas[-1]] + [preds[t] for t in pred_targets]
            fig.add_trace(go.Scatter(
                x=px_, y=py_, mode='lines+markers',
                name=f"{mi['icon']} {mname}",
                line=dict(color=mi['color'], width=2, dash='dash'),
                marker=dict(size=7, color=mi['color'], line=dict(color='white', width=1.5)),
                hovertemplate=f'%{{x}} ({mname}): %{{y:.3f}}<extra></extra>'
            ))
        fig.update_layout(
            plot_bgcolor='#FAFBFD', paper_bgcolor=db.CARD, font=db.FONT,
            height=420, margin=dict(t=60, b=80, l=64, r=40), showlegend=True,
            legend=dict(orientation='h', y=-0.3, x=0.5, xanchor='center',
                        bgcolor='rgba(0,0,0,0)', font=dict(size=11, color=db.TX2)),
            hoverlabel=dict(bgcolor='white', font_size=13, font_color='#1E2A3A', bordercolor='#1E2A3A', font_family='Noto Sans Lao,Segoe UI,Arial,sans-serif'))
        fig.update_xaxes(showgrid=False, zeroline=False, color=db.TX, title_text='ພາກຮຽນ')
        fig.update_yaxes(showgrid=True, gridcolor='#EEF0F5', zeroline=False,
                         range=[0, 4.3], title_text='GPA')

        header = [
            html.Th('ພາກ', style={**LAO, 'padding': '10px 12px', 'background': '#F0F4FF',
                                   'color': db.TX, 'fontSize': '12px', 'fontWeight': '600'}),
            html.Th('GPA ຕົວຈິງ ✓', style={**LAO, 'padding': '10px 12px', 'background': '#F0F4FF',
                                    'color': '#000', 'fontSize': '12px', 'fontWeight': '700', 'textAlign': 'center'}),
        ] + [html.Th(f"{MODEL_INFO.get(m, {}).get('icon', '')} {m}",
                     style={**LAO, 'padding': '10px 10px', 'background': '#F0F4FF',
                            'color': MODEL_INFO.get(m, {}).get('color', db.TX), 'fontSize': '11px',
                            'fontWeight': '600', 'textAlign': 'center', 'whiteSpace': 'nowrap'})
             for m in all_preds]

        rows = []
        for t in pred_targets:
            act = actual.get(t)
            cells = [
                html.Td(db.sem_order[t - 1], style={**LAO, 'padding': '8px 12px',
                         'fontWeight': '600', 'color': db.TX2, 'fontSize': '13px'}),
                html.Td(str(act) if act else '—',
                        style={**LAO, 'padding': '8px 12px', 'textAlign': 'center',
                               'fontWeight': '700', 'color': '#000', 'fontSize': '13px'}),
            ]
            for mname in all_preds:
                mi = MODEL_INFO.get(mname, {'color': db.TX})
                pv = all_preds[mname].get(t)
                err = round(abs(pv - act), 3) if act and pv is not None else None
                cells.append(html.Td(style={'padding': '8px 10px', 'textAlign': 'center'}, children=[
                    html.Div(str(pv), style={'fontWeight': '600', 'color': mi['color'], 'fontSize': '13px'}),
                    html.Div(f'err:{err}', style={**LAO, 'fontSize': '10px',
                        'color': db.RED if (err and err > 0.3) else db.GREEN}) if err is not None else None
                ]))
            rows.append(html.Tr(style={'background': '#FAFBFD' if t % 2 == 0 else 'white',
                                        'borderBottom': f'1px solid {db.BD}'}, children=cells))

        stage_metrics = PREDICTOR.stages.get(known_k, {}).get('metrics', {})
        rmse_cards = []
        for mname in all_preds:
            mi = MODEL_INFO.get(mname, {'color': db.TX, 'icon': ''})
            errs = [(all_preds[mname].get(t, 0) - actual.get(t, 0)) ** 2
                    for t in pred_targets if actual.get(t) and all_preds[mname].get(t)]
            rmse_vs = round(np.sqrt(np.mean(errs)), 4) if errs else None
            cv_rmse = stage_metrics.get(mname, {}).get('rmse')
            rmse_cards.append(html.Div(style={
                'flex': '1', 'minWidth': '130px', 'textAlign': 'center',
                'background': 'white', 'borderRadius': '10px', 'padding': '12px 8px',
                'border': f'2px solid {mi["color"]}',
            }, children=[
                html.Div(f"{mi['icon']} {mname}",
                         style={**LAO, 'fontSize': '11px', 'fontWeight': '700',
                                'color': mi['color'], 'marginBottom': '6px'}),
                html.Div(str(rmse_vs) if rmse_vs else '—',
                         style={'fontSize': '20px', 'fontWeight': '700',
                                'color': db.RED if (rmse_vs and rmse_vs > 0.4) else db.GREEN}),
                html.Div('RMSE vs ຈິງ' if rmse_vs else '(ບໍ່ມີຂໍ້ມູນຈິງ)',
                         style={**LAO, 'fontSize': '9px', 'color': db.TX, 'marginTop': '2px'}),
                html.Div(f'CV: ±{cv_rmse}' if cv_rmse else '',
                         style={**LAO, 'fontSize': '9px', 'color': '#90A4AE', 'marginTop': '1px'}),
            ]))

        if actual and any(actual.get(t) for t in pred_targets):
            best_m = min(all_preds, key=lambda m: sum(
                (all_preds[m].get(t, 0) - actual.get(t, 0)) ** 2
                for t in pred_targets if actual.get(t)))
        else:
            best_m = min(stage_metrics, key=lambda m: stage_metrics[m]['rmse']) if stage_metrics else list(all_preds)[0]

        bmi = MODEL_INFO.get(best_m, {'icon': '📈', 'color': db.BLUE})
        final_gpa = all_preds[best_m][8]
        cl_name, cl_color = classify(final_gpa)
        avg_cv = round(np.mean([stage_metrics[m]['rmse'] for m in stage_metrics]), 4) if stage_metrics else None
        trend = analyze_trend(actual)

        if trend:
            mark_idx = trend['mark_sem_idx']
            fig.add_annotation(
                x=db.sem_order[mark_idx - 1], y=actual[mark_idx],
                text=trend['mark_icon'], showarrow=True, arrowhead=2, arrowsize=1.2,
                arrowcolor='#C62828' if trend['severity'] == 'critical' else '#E65100',
                ax=0, ay=-45, font=dict(size=22),
                bgcolor='white', bordercolor='#C62828' if trend['severity'] == 'critical' else '#E65100',
                borderwidth=1.5, borderpad=4,
            )

        return html.Div([
            html.Div(style={
                'background': f'{cl_color}15', 'border': f'2px solid {cl_color}',
                'borderRadius': '12px', 'padding': '16px 20px', 'marginBottom': '16px',
                'display': 'flex', 'alignItems': 'center', 'gap': '14px'
            }, children=[
                html.Div('🌟' if cl_name == 'ສູງ' else ('⚠️' if cl_name == 'ສ່ຽງ' else '📊'),
                         style={'fontSize': '36px'}),
                html.Div([
                    html.Div(f'{bmi["icon"]} {best_m} — ຜົນການຄາດຄະເນ',
                             style={**LAO, 'fontSize': '16px', 'fontWeight': '700', 'color': cl_color}),
                    html.Div(f'GPA ຄາດຄະເນ ພາກ 4/II ≈ {final_gpa:.3f} · ກຸ່ມ: {cl_name}',
                             style={**LAO, 'fontSize': '13px', 'color': db.TX, 'marginTop': '3px'}),
                    html.Div(f'⚠️ RMSE ສະເລ່ຍ ±{avg_cv} GPA — ຄາດຄະເນໄດ້ລະດັບກຸ່ມ ບໍ່ແມ່ນ GPA ທີ່ແນ່ນອນ' if avg_cv else '',
                             style={**LAO, 'fontSize': '11px', 'color': '#B71C1C', 'marginTop': '3px'}),
                ])
            ]),
            html.Div(style=db.card_style('#E65100'), children=[
                db.sec_title('🧠 Multi-Output — ຜົນການຄາດຄະເນ'),
                db.sec_sub('RMSE vs ຈິງ = ຄວາມຜິດພາດຈາກຂໍ້ມູນຈິງ · CV = Cross-Validation'),
                html.Div(style={'display': 'flex', 'gap': '10px', 'flexWrap': 'wrap', 'marginTop': '8px'},
                         children=rmse_cards),
            ]),
            html.Div(style=db.card_style('#6A1B9A'), children=[
                db.sec_title('ກາຟ GPA ຕົວຈິງ VS GPA ຄາດຄະເນ'),
                db.sec_sub(f'ດຳ = ຂໍ້ມູນຈິງ · ຟ້າ = {known_k} ພາກທີ່ໃສ່ · ເສັ້ນປະ = ຄາດຄະເນພາກທີ່ເຫຼືອ'),
                dcc.Graph(figure=fig, config={'displayModeBar': False}),
            ]),
            html.Div(style=db.card_style(db.BLUE), children=[
                db.sec_title('ຕາຕະລາງ GPA ຕົວຈິງ VS GPA ຄາດຄະເນ'),
                db.sec_sub('GPA ຕົວຈິງ VS GPA ຄາດຄະເນ · ຂຽວ ≤ 0.3 · ແດງ > 0.3'),
                html.Div(style={'overflowX': 'auto', 'borderRadius': '10px',
                                'border': f'1px solid {db.BD}', 'marginTop': '12px'}, children=[
                    html.Table(className='pred-result-table', style={'width': '100%', 'borderCollapse': 'collapse'}, children=[
                        html.Thead(html.Tr(children=header)),
                        html.Tbody(children=rows)
                    ])
                ]) if rows else html.Div('ເລືອກ ນ.ສ ທີ່ມີຂໍ້ມູນຈິງ ເພື່ອເບິ່ງການປຽບທຽບ',
                    style={**LAO, 'color': db.TX, 'fontSize': '13px', 'padding': '12px'})
            ]),
            html.Div(style={
                'background': '#FFF3E0' if trend['severity'] == 'warning' else '#FFEBEE',
                'border': f"1px solid {'#FFB74D' if trend['severity'] == 'warning' else '#FFCDD2'}",
                'borderRadius': '10px', 'padding': '14px 16px', 'marginTop': '4px',
            }, children=[
                html.Div(trend['title'],
                         style={**LAO, 'fontWeight': '700',
                                'color': '#E65100' if trend['severity'] == 'warning' else db.RED,
                                'marginBottom': '4px'}),
                html.Div(trend['detail'],
                         style={**LAO, 'fontSize': '12px', 'color': db.TX, 'marginBottom': '8px'}),
                html.Div('ຄວນເຮັດຫຍັງຕໍ່:', style={**LAO, 'fontSize': '12px', 'fontWeight': '600', 'color': db.TX2}),
                html.Ul(style={**LAO, 'fontSize': '13px', 'color': '#B71C1C',
                               'paddingLeft': '20px', 'lineHeight': '2', 'marginTop': '4px'},
                        children=[html.Li(a) for a in trend['actions']]),
            ]) if trend else None,
            html.Div(style={'background': '#FFEBEE', 'border': '1px solid #FFCDD2',
                            'borderRadius': '10px', 'padding': '14px 16px', 'marginTop': '4px'}, children=[
                html.Div('⚠️ ຄຳແນະນຳສຳລັບກຸ່ມ ສ່ຽງ',
                         style={**LAO, 'fontWeight': '700', 'color': db.RED, 'marginBottom': '8px'}),
                html.Ul(style={**LAO, 'fontSize': '13px', 'color': '#B71C1C',
                               'paddingLeft': '20px', 'lineHeight': '2'}, children=[
                    html.Li('ຕິດຕໍ່ອາຈານທີ່ປຶກສາ ເພື່ອວາງແຜນການຮຽນ'),
                    html.Li('ກວດສອບວິຊາທີ່ໄດ້ F ຫຼື D ແລ້ວວາງແຜນລົງທະບຽນຊ້ຳ'),
                    html.Li('ເຂົ້າຮຽນໃຫ້ຄົບ ແລະ ສົ່ງວຽກໃຫ້ທັນເວລາ'),
                ])
            ]) if cl_name == 'ສ່ຽງ' else None,
        ])


def build_real_acc_card(acc):
    if not acc:
        return html.Div()
    sem_names = ['1/II', '2/I', '2/II', '3/I', '3/II', '4/I', '4/II']
    n_stu = acc.get('n_students', '?')
    overall = acc.get('ລວມ', {})
    rows = []
    for i, s in enumerate(sem_names):
        d = acc.get(s, {})
        rmse = d.get('rmse', '—')
        mae = d.get('mae', '—')
        color = db.GREEN if isinstance(rmse, float) and rmse < 0.5 else (
            '#E65100' if isinstance(rmse, float) and rmse < 0.7 else db.RED)
        rows.append(html.Tr(style={
            'background': '#FAFBFD' if i % 2 == 0 else 'white',
            'borderBottom': f'1px solid {db.BD}'
        }, children=[
            html.Td(s, style={**LAO, 'padding': '8px 14px', 'fontWeight': '600', 'color': db.TX2, 'fontSize': '13px'}),
            html.Td(str(rmse), style={'padding': '8px 14px', 'textAlign': 'center', 'fontWeight': '700',
                                       'color': color, 'fontSize': '13px'}),
            html.Td(str(mae), style={'padding': '8px 14px', 'textAlign': 'center', 'color': db.TX, 'fontSize': '12px'}),
        ]))
    ovr_rmse = overall.get('rmse', '—')
    rows.append(html.Tr(style={'background': '#E8F5E9', 'borderTop': f'2px solid {db.GREEN}'}, children=[
        html.Td('ລວມທຸກພາກ', style={**LAO, 'padding': '10px 14px', 'fontWeight': '700', 'color': db.GREEN, 'fontSize': '13px'}),
        html.Td(str(ovr_rmse), style={'padding': '10px 14px', 'textAlign': 'center', 'fontWeight': '700',
                                       'color': db.GREEN, 'fontSize': '15px'}),
        html.Td(str(overall.get('mae', '—')), style={'padding': '10px 14px', 'textAlign': 'center', 'color': db.TX, 'fontSize': '12px'}),
    ]))
    return html.Div(style={**db.card_style('#375623')}, children=[
        db.sec_title('🎯 ຄວາມແມ່ນຍຳຕາມຂໍ້ມູນຈິງ — ຄາດຄະເນຈາກ 1/I ພາກດຽວ'),
        db.sec_sub(f'ທົດສອບກັບ {n_stu} ນ.ສ ທີ່ມີຂໍ້ມູນຄົບ 8 ພາກ · RMSE = |ຄາດຄະເນ − ຕົວຈິງ| · ຕ່ຳ = ດີ'),
        html.Div(style={'overflowX': 'auto', 'borderRadius': '10px', 'border': f'1px solid {db.BD}', 'marginTop': '12px'},
                 children=[html.Table(style={'width': '100%', 'borderCollapse': 'collapse'}, children=[
            html.Thead(html.Tr(children=[
                html.Th('ພາກ', style={**LAO, 'padding': '10px 14px', 'background': '#F0F4FF', 'color': db.TX, 'fontSize': '12px', 'fontWeight': '600'}),
                html.Th('RMSE', style={**LAO, 'padding': '10px 14px', 'background': '#F0F4FF', 'color': db.TX, 'fontSize': '12px', 'fontWeight': '600', 'textAlign': 'center'}),
                html.Th('MAE', style={**LAO, 'padding': '10px 14px', 'background': '#F0F4FF', 'color': db.TX, 'fontSize': '12px', 'fontWeight': '600', 'textAlign': 'center'}),
            ])),
            html.Tbody(children=rows)
        ])])
    ])


def build_rmse_table(trained):
    if not trained:
        return html.Div('⚠️ ຍັງບໍ່ມີໂມເດລ — ກົດ "ເທຣນໂມເດລໃໝ່"',
                        style={**LAO, 'color': db.RED, 'fontSize': '13px', 'padding': '12px'})
    rows = [html.Tr(children=[
        html.Td(f"{MODEL_INFO.get(m, {}).get('icon', '')} {m}",
                style={**LAO, 'padding': '10px 14px', 'fontWeight': '700',
                       'color': MODEL_INFO.get(m, {}).get('color', db.TX), 'fontSize': '13px'}),
        html.Td(str(trained[m]['rmse']),
                style={'padding': '10px 14px', 'textAlign': 'center',
                       'fontWeight': '600', 'fontSize': '14px',
                       'color': db.RED if trained[m]['rmse'] > 0.5 else db.GREEN}),
    ], style={'borderBottom': f'1px solid {db.BD}',
              'background': '#FAFBFD' if i % 2 == 0 else 'white'})
            for i, m in enumerate(sorted(trained, key=lambda x: trained[x]['rmse']))]

    best_m = min(trained, key=lambda m: trained[m]['rmse'])
    return html.Div(style=db.card_style('#E65100'), children=[
        db.sec_title('🧠 Multi-Output — RMSE (5-Fold Cross-Validation)'),
        db.sec_sub(f'ດີທີ່ສຸດ: {best_m} RMSE={trained[best_m]["rmse"]} · ຕ່ຳ = ດີ'),
        html.Div(style={'overflowX': 'auto', 'borderRadius': '10px', 'border': f'1px solid {db.BD}'}, children=[
            html.Table(style={'width': '100%', 'borderCollapse': 'collapse'}, children=[
                html.Thead(html.Tr(children=[
                    html.Th('ໂມເດລ', style={**LAO, 'padding': '10px 14px', 'background': '#F0F4FF',
                                            'color': db.TX, 'fontSize': '12px', 'fontWeight': '600'}),
                    html.Th('RMSE (CV)', style={**LAO, 'padding': '10px 14px', 'background': '#F0F4FF',
                                                  'color': db.TX, 'fontSize': '12px', 'fontWeight': '600',
                                                  'textAlign': 'center'}),
                ])),
                html.Tbody(children=rows)
            ])
        ])
    ])
