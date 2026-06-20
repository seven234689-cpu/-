from dash import html, dcc, Input, Output, State
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

student_opts = [
    {'label': f"{r['student_code']} · {'ຊາຍ' if r['gender'] == 'M' else 'ຍິງ'}", 'value': r['student_code']}
    for _, r in db.df_student.sort_values('student_code').iterrows()
] if len(db.df_student) > 0 else []


layout = html.Div(style={'padding': '28px 32px', 'background': db.PAGE, 'minHeight': '100vh'}, children=[

    html.Div(style={'marginBottom': '24px'}, children=[
        html.Div('ວິເຄາະແນວໂນ້ມ GPA', style={'fontSize': '22px', 'fontWeight': '700', 'color': db.TX2}),
        html.Div('Multi-Output · Random Forest / XGBoost · ປ້ອນ 1/I → ທຳນາຍ 7 ພາກທີ່ເຫຼືອ',
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
            html.Div('⚠️  ຕົວເລກ GPA ທີ່ສະແດງ ແມ່ນພຽງຄ່າປະມານການ ບໍ່ໃຊ່ GPA ທີ່ແນ່ນອນ',
                     style={**LAO, 'fontSize': '13px', 'fontWeight': '700', 'color': '#C62828'}),
            html.Div('📊  ໃຊ້ GPA ພາກ 1/I ເປັນຂໍ້ມູນເຂົ້າ → ທຳນາຍ 7 ພາກທີ່ເຫຼືອພ້ອມກັນ',
                     style={**LAO, 'fontSize': '12px', 'color': '#B71C1C', 'marginTop': '4px'}),
            html.Div('✅  ໃຊ້ເພື່ອສັງເກດແນວໂນ້ມເທົ່ານັ້ນ ຢ່າໃຊ້ຕັດສິນໃຈສຳຄັນ',
                     style={**LAO, 'fontSize': '12px', 'color': '#B71C1C'}),
        ])
    ]),

    html.Div(id='pred-rmse-table', style={'marginBottom': '20px'}),
    html.Div(id='pred-real-acc', style={'marginBottom': '20px'}),

    html.Div(style=db.card_style(db.BLUE), children=[
        db.sec_title('ເລືອກ ນ.ສ ຫຼື ປ້ອນ GPA ພາກ 1/I'),
        db.sec_sub('ປ້ອນ GPA ພາກ 1/I ເທົ່ານັ້ນ · ໂມເດລຈະທຳນາຍ 7 ພາກທີ່ເຫຼືອພ້ອມກັນ'),

        html.Div(style={'marginBottom': '12px'}, children=[
            html.Label('ເລືອກ ນ.ສ', style={**LAO, 'fontSize': '12px', 'fontWeight': '600',
                       'color': db.TX, 'display': 'block', 'marginBottom': '6px'}),
            dcc.Dropdown(id='pred-student-dd', options=student_opts,
                         placeholder='ຄົ້ນຫາ ຫຼື ເລືອກ ນ.ສ...', searchable=True, clearable=True,
                         style={'fontSize': '13px'}),
        ]),

        html.Div(style={'display': 'flex', 'gap': '10px', 'marginBottom': '16px'}, children=[
            html.Button('📂 ໂຫລດຂໍ້ມູນ ນ.ສ', id='pred-load-btn', n_clicks=0,
                        style={'padding': '10px 24px', 'background': db.BLUE, 'color': 'white',
                               'border': 'none', 'borderRadius': '8px', 'fontSize': '13px', 'fontWeight': '600',
                               'cursor': 'pointer', 'fontFamily': 'Noto Sans Lao,Segoe UI,Arial,sans-serif'}),
            html.Button('🏆 ເທຣນໂມເດລໃໝ່', id='pred-retrain-btn', n_clicks=0,
                        style={'padding': '10px 24px', 'background': '#E65100', 'color': 'white',
                               'border': 'none', 'borderRadius': '8px', 'fontSize': '13px', 'fontWeight': '600',
                               'cursor': 'pointer', 'fontFamily': 'Noto Sans Lao,Segoe UI,Arial,sans-serif'}),
        ]),

        html.Div(id='pred-train-status'),
        html.Hr(style={'border': 'none', 'borderTop': f'1px solid {db.BD}', 'margin': '12px 0 16px 0'}),

        html.Div(style={'marginBottom': '16px'}, children=[
            html.Label('GPA ພາກ 1/I (ຂໍ້ມູນເຂົ້າ)', style={**LAO, 'fontSize': '12px', 'fontWeight': '600',
                       'color': db.TX, 'display': 'block', 'marginBottom': '6px'}),
            dcc.Input(id='pred-sem-1', type='number', min=0.0, max=4.0, step=0.01,
                      style={'width': '120px', 'padding': '8px 12px', 'fontSize': '14px',
                             'borderRadius': '8px', 'border': f'1px solid {db.BD}'}),
        ]),

        html.Div(id='pred-gpa-preview', style={'marginBottom': '16px'}),

        html.Div(style={'display': 'none'}, children=[
            *[dcc.Input(id=f'pred-sem-{i}', type='number', min=0.0, max=4.0, step=0.01)
              for i in range(2, 9)]
        ]),

        html.Button('🔮 ທຳນາຍ GPA 7 ພາກທີ່ເຫຼືອ', id='pred-btn', n_clicks=0,
                    style={'padding': '12px 32px', 'background': db.BLUE, 'color': 'white',
                           'border': 'none', 'borderRadius': '8px', 'fontSize': '14px', 'fontWeight': '600',
                           'cursor': 'pointer', 'fontFamily': 'Noto Sans Lao,Segoe UI,Arial,sans-serif'}),
    ]),

    html.Div(id='pred-result', style={'marginTop': '20px'}),
])


def register_callbacks(app):

    @app.callback(Output('pred-real-acc', 'children'), Input('pred-real-acc', 'id'))
    def show_real_acc(_):
        return build_real_acc_card(REAL_ACC)

    @app.callback(Output('pred-rmse-table', 'children'), Input('pred-rmse-table', 'id'))
    def show_rmse(_):
        return build_rmse_table(ALL_MODELS)

    @app.callback(
        [Output('pred-sem-1', 'value')] +
        [Output(f'pred-sem-{i}', 'value') for i in range(2, 9)] +
        [Output('pred-gpa-preview', 'children')] +
        [Output('pred-train-status', 'children')],
        Input('pred-load-btn', 'n_clicks'),
        State('pred-student-dd', 'value'),
        prevent_initial_call=True
    )
    def load_student(n, code):
        if not code:
            return [None] + [None] * 7 + [html.Div()] + [html.Div('⚠️ ກະລຸນາເລືອກ ນ.ສ ກ່ອນ',
                style={**LAO, 'color': db.RED, 'fontSize': '13px'})]

        sc = db.df[db.df['student_code'] == code].copy()
        sc['sem_idx'] = sc['semester'].map(sem_order_map)
        gpa = sc.groupby('sem_idx')['grade_point'].mean().round(3).to_dict()
        sem1 = gpa.get(1)
        actual_rest = [gpa.get(i) for i in range(2, 9)]
        n_all = len(gpa)

        note = ('⭐ ຂໍ້ມູນຄົບ 8 ພາກ — ຈະສະແດງ ທຳນາຍ vs ຈິງ' if n_all == 8 else
                f'ໃຊ້ GPA 1/I = {sem1} · ທຳນາຍ 7 ພາກທີ່ເຫຼືອ')
        status = html.Div(style={'background': '#E8F5E9', 'border': '1px solid #A5D6A7',
                                  'borderRadius': '8px', 'padding': '10px 14px'}, children=[
            html.Div(f'✅ ໂຫລດສຳເລັດ — {code}',
                     style={**LAO, 'fontSize': '13px', 'fontWeight': '600', 'color': '#2E7D32'}),
            html.Div(note, style={**LAO, 'fontSize': '11px', 'color': db.TX, 'marginTop': '4px'}),
        ])

        sem_names = ['1/I', '1/II', '2/I', '2/II', '3/I', '3/II', '4/I', '4/II']
        preview_items = []
        for i, v in enumerate([sem1] + actual_rest, 1):
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

        return [sem1] + actual_rest + [preview] + [status]

    @app.callback(
        Output('pred-rmse-table', 'children', allow_duplicate=True),
        Output('pred-train-status', 'children', allow_duplicate=True),
        Input('pred-retrain-btn', 'n_clicks'),
        prevent_initial_call=True
    )
    def retrain(n):
        global PREDICTOR, ALL_MODELS, REAL_ACC, HIGH_THR, RISK_THR
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
        Input('pred-btn', 'n_clicks'),
        [State('pred-sem-1', 'value')] +
        [State(f'pred-sem-{i}', 'value') for i in range(2, 9)] +
        [State('pred-student-dd', 'value')],
        prevent_initial_call=True
    )
    def predict(n_clicks, sem1, *args):
        actual_vals = args[:7]
        code = args[7]

        if not sem1 or not (0.0 <= float(sem1) <= 4.0):
            return html.Div('⚠️ ກະລຸນາໃສ່ GPA ພາກ 1/I ກ່ອນ (0.00 – 4.00)',
                            style={**LAO, 'color': db.RED, 'fontSize': '14px', 'padding': '12px'})

        if not PREDICTOR.is_ready:
            return html.Div('⚠️ ຍັງບໍ່ມີໂມເດລ — ກົດ "ເທຣນໂມເດລໃໝ່" ກ່ອນ',
                            style={**LAO, 'color': db.RED, 'fontSize': '14px', 'padding': '12px'})

        gpa_1 = round(float(sem1), 3)
        known = {1: gpa_1}

        fr_1, ns_1, gender, major = 0.0, 0.0, 0, None
        gpa_1_std, gpa_1_min, weak_1 = 0.0, gpa_1, 0.0
        actual = {}
        if code:
            sc = db.df[db.df['student_code'] == code].copy()
            sc['sem_idx'] = sc['semester'].map(sem_order_map)
            actual = sc.groupby('sem_idx')['grade_point'].mean().round(3).to_dict()
            if 1 in sc['sem_idx'].values:
                s1 = sc[sc['sem_idx'] == 1]
                fr_1 = float((s1['grade'] == 'F').mean())
                ns_1 = float(len(s1))
                gpa_1_std = float(s1['grade_point'].std() or 0.0)
                gpa_1_min = float(s1['grade_point'].min())
                weak_1 = float((s1['grade_point'] <= 2.0).sum())
            stu = db.df_student[db.df_student['student_code'] == code]
            gender = 1 if stu['gender'].values[0] == 'F' else 0
            major = stu['major'].values[0] if 'major' in stu.columns else None

        all_preds = PREDICTOR.predict_all(
            gpa_1, gender=gender, fr_1=fr_1, ns_1=ns_1, major=major,
            gpa_1_std=gpa_1_std, gpa_1_min=gpa_1_min, weak_1=weak_1,
        )
        pred_targets = list(range(2, 9))

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
                x=ax, y=ay, mode='lines+markers', name='GPA ຈິງ',
                line=dict(color='#000', width=3),
                marker=dict(size=10, color='black', line=dict(color='white', width=2)),
                hovertemplate='%{x} (ຈິງ): %{y:.3f}<extra></extra>'
            ))
        fig.add_trace(go.Scatter(
            x=[db.sem_order[0]], y=[gpa_1],
            mode='markers', name='GPA ທີ່ໃສ່ (1/I)',
            marker=dict(size=14, color=db.BLUE, line=dict(color='white', width=2.5)),
            hovertemplate='1/I (ໃສ່): %{y:.3f}<extra></extra>'
        ))
        for mname, preds in all_preds.items():
            mi = MODEL_INFO.get(mname, {'color': '#666', 'icon': '📈'})
            px_ = [db.sem_order[0]] + [db.sem_order[k - 1] for k in pred_targets]
            py_ = [gpa_1] + [preds[k] for k in pred_targets]
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
            hoverlabel=dict(bgcolor='white', font_size=13, bordercolor=db.BD))
        fig.update_xaxes(showgrid=False, zeroline=False, color=db.TX, title_text='ພາກຮຽນ')
        fig.update_yaxes(showgrid=True, gridcolor='#EEF0F5', zeroline=False,
                         range=[0, 4.3], title_text='GPA')

        header = [
            html.Th('ພາກ', style={**LAO, 'padding': '10px 12px', 'background': '#F0F4FF',
                                   'color': db.TX, 'fontSize': '12px', 'fontWeight': '600'}),
            html.Th('ຈິງ ✓', style={**LAO, 'padding': '10px 12px', 'background': '#F0F4FF',
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

        rmse_cards = []
        for mname in all_preds:
            mi = MODEL_INFO.get(mname, {'color': db.TX, 'icon': ''})
            errs = [(all_preds[mname].get(t, 0) - actual.get(t, 0)) ** 2
                    for t in pred_targets if actual.get(t) and all_preds[mname].get(t)]
            rmse_vs = round(np.sqrt(np.mean(errs)), 4) if errs else None
            cv_rmse = ALL_MODELS.get(mname, {}).get('rmse')
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
            best_m = min(ALL_MODELS, key=lambda m: ALL_MODELS[m]['rmse']) if ALL_MODELS else list(all_preds)[0]

        bmi = MODEL_INFO.get(best_m, {'icon': '📈', 'color': db.BLUE})
        final_gpa = all_preds[best_m][8]
        cl_name, cl_color = classify(final_gpa)
        avg_cv = round(np.mean([ALL_MODELS[m]['rmse'] for m in ALL_MODELS]), 4) if ALL_MODELS else None

        return html.Div([
            html.Div(style={
                'background': f'{cl_color}15', 'border': f'2px solid {cl_color}',
                'borderRadius': '12px', 'padding': '16px 20px', 'marginBottom': '16px',
                'display': 'flex', 'alignItems': 'center', 'gap': '14px'
            }, children=[
                html.Div('🌟' if cl_name == 'ສູງ' else ('⚠️' if cl_name == 'ສ່ຽງ' else '📊'),
                         style={'fontSize': '36px'}),
                html.Div([
                    html.Div(f'{bmi["icon"]} {best_m} — ຜົນການທຳນາຍ',
                             style={**LAO, 'fontSize': '16px', 'fontWeight': '700', 'color': cl_color}),
                    html.Div(f'GPA ທຳນາຍ ພາກ 4/II ≈ {final_gpa:.3f} · ກຸ່ມ: {cl_name}',
                             style={**LAO, 'fontSize': '13px', 'color': db.TX, 'marginTop': '3px'}),
                    html.Div(f'⚠️ RMSE ສະເລ່ຍ ±{avg_cv} GPA — ທຳນາຍໄດ້ລະດັບກຸ່ມ ບໍ່ໃຊ່ GPA ທີ່ແນ່ນອນ' if avg_cv else '',
                             style={**LAO, 'fontSize': '11px', 'color': '#B71C1C', 'marginTop': '3px'}),
                ])
            ]),
            html.Div(style=db.card_style('#E65100'), children=[
                db.sec_title('🧠 Multi-Output — ຜົນການທຳນາຍ'),
                db.sec_sub('RMSE vs ຈິງ = ຄວາມຜິດພາດຈາກຂໍ້ມູນຈິງ · CV = Cross-Validation'),
                html.Div(style={'display': 'flex', 'gap': '10px', 'flexWrap': 'wrap', 'marginTop': '8px'},
                         children=rmse_cards),
            ]),
            html.Div(style=db.card_style('#6A1B9A'), children=[
                db.sec_title('ກາຟ ທຳນາຍ vs ຈິງ'),
                db.sec_sub('ດຳ = ຂໍ້ມູນຈິງ · ຟ້າ = 1/I ທີ່ໃສ່ · ເສັ້ນປະ = ທຳນາຍ 7 ພາກທີ່ເຫຼືອ'),
                dcc.Graph(figure=fig, config={'displayModeBar': False}),
            ]),
            html.Div(style=db.card_style(db.BLUE), children=[
                db.sec_title('ຕາຕະລາງ ທຳນາຍ vs ຈິງ'),
                db.sec_sub('err = |ທຳນາຍ − ຈິງ| · ຂຽວ ≤ 0.3 · ແດງ > 0.3'),
                html.Div(style={'overflowX': 'auto', 'borderRadius': '10px',
                                'border': f'1px solid {db.BD}', 'marginTop': '12px'}, children=[
                    html.Table(style={'width': '100%', 'borderCollapse': 'collapse'}, children=[
                        html.Thead(html.Tr(children=header)),
                        html.Tbody(children=rows)
                    ])
                ]) if rows else html.Div('ເລືອກ ນ.ສ ທີ່ມີຂໍ້ມູນຈິງ ເພື່ອເບິ່ງການປຽບທຽບ',
                    style={**LAO, 'color': db.TX, 'fontSize': '13px', 'padding': '12px'})
            ]),
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
        db.sec_title('🎯 ຄວາມແມ່ນຍຳຕາມຂໍ້ມູນຈິງ — ທຳນາຍຈາກ 1/I ພາກດຽວ'),
        db.sec_sub(f'ທົດສອບກັບ {n_stu} ນ.ສ ທີ່ມີຂໍ້ມູນຄົບ 8 ພາກ · RMSE = |ທຳນາຍ − ຈິງ| · ຕ່ຳ = ດີ'),
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
