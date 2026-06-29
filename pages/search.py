from dash import html, dcc, Input, Output, dash_table
import plotly.graph_objects as go
import db

LAO = {'fontFamily': 'Noto Sans Lao,Segoe UI,Arial,sans-serif'}
sem_order_map = {s: i+1 for i, s in enumerate(db.sem_order)}

def _student_opts():
    return [
        {'label': f"{r['student_code']}  ·  {'ຊາຍ' if r['gender']=='M' else 'ຍິງ'}",
         'value': r['student_code']}
        for _, r in db.df_student.sort_values('student_code').iterrows()
    ]


def layout():
    return html.Div(style={'padding': '28px 32px', 'background': db.PAGE, 'minHeight': '100vh'}, children=[
    html.Div(style={'marginBottom': '24px'}, children=[
        html.Div('ຄົ້ນຫານັກສຶກສາ', style={'fontSize': '22px', 'fontWeight': '700', 'color': db.TX2}),
        html.Div('ເລືອກລະຫັດ ນ.ສ ເພື່ອເບິ່ງ GPA Trend ທຸກພາກ ແລະ ເກຣດທຸກວິຊາ',
                 style={**LAO, 'fontSize': '13px', 'color': db.TX, 'marginTop': '4px'}),
    ]),
    html.Div(style=db.card_style('#6A1B9A'), children=[
        db.sec_title('ຄົ້ນຫາ'),
        db.sec_sub('ພິມ ຫຼື ເລືອກລະຫັດ ນ.ສ ຈາກລາຍການ'),

        # ── ຄົ້ນຫາ ນ.ສ ──────────────────────────────────────
        dcc.Dropdown(
            id='search-dd',
            options=_student_opts(),
            placeholder='ຄົ້ນຫາ... ເຊັ່ນ 205N0001.19',
            searchable=True, clearable=True,
            persistence=True, persistence_type='memory',
            style={'fontSize': '13px', 'marginBottom': '12px'}
        ),

        html.Div(id='search-result', style={'marginTop': '8px'})
    ]),
])


def register_callbacks(app):

    @app.callback(
        Output('search-result', 'children'),
        Input('search-dd', 'value'),
    )
    def show(code):
        sem_only = 'all'
        sem_from = '1/I'
        sem_to   = '4/II'
        if not code:
            return html.Div(style={
                'textAlign': 'center', 'padding': '36px',
                'border': f'1.5px dashed {db.BD}', 'borderRadius': '12px',
                'background': db.PAGE
            }, children=[
                html.Div('ເລືອກ ນ.ສ ດ້ານເທິງ ເພື່ອເບິ່ງຂໍ້ມູນ',
                         style={**LAO, 'color': '#90A4AE', 'fontSize': '13px', 'fontWeight': '500'}),
            ])

        stu = db.df_gpa[db.df_gpa['student_code'] == code]
        if stu.empty:
            return html.Div('ບໍ່ພົບຂໍ້ມູນ', style={**LAO, 'color': db.RED})

        gen_v   = 'ຊາຍ' if stu.iloc[0]['gender'] == 'M' else 'ຍິງ'
        cl_v    = stu.iloc[0]['cluster']
        cl_c    = db.CC.get(cl_v, '#546078')
        major_v = stu.iloc[0]['major'] if 'major' in stu.columns and stu.iloc[0].get('major') else 'ບໍ່ລະບຸ'

        # ── ດຶງຂໍ້ມູນທຸກພາກ ──────────────────────────────────
        sc_all = db.df[db.df['student_code'] == code].copy()
        sc_all['_sort'] = sc_all['semester'].map(sem_order_map)
        sc_all = sc_all.sort_values('_sort')

        # ── ກໍານົດ range ──────────────────────────────────────
        idx_from = sem_order_map.get(sem_from, 1)
        idx_to   = sem_order_map.get(sem_to, 8)
        if idx_from > idx_to:
            idx_from, idx_to = idx_to, idx_from

        # filter ສໍາລັບ KPI + ຕາຕະລາງ
        if sem_only != 'all':
            sc_show = sc_all[sc_all['semester'] == sem_only]
            range_label = f'ສະເພາະ {sem_only}'
        else:
            sc_show = sc_all[(sc_all['_sort'] >= idx_from) & (sc_all['_sort'] <= idx_to)]
            range_label = f'{sem_from} → {sem_to}'

        # GPA ໃນ range
        gpa_range = round(sc_show['grade_point'].mean(), 3) if len(sc_show) > 0 else 0.0
        gpa_all   = stu.iloc[0]['gpa']  # GPA ລວມທຸກພາກ
        fc = int((sc_show['grade'] == 'F').sum())
        ac = int((sc_show['grade'] == 'A').sum())
        n_subj = len(sc_show)

        # ── GPA Trend (ທຸກພາກ + highlight range) ─────────────
        sg = (sc_all.groupby('semester')['grade_point']
              .mean().reset_index(name='gpa'))
        sg['_sort'] = sg['semester'].map(sem_order_map)
        sg = sg.sort_values('_sort')
        sg['gpa'] = sg['gpa'].round(2)
        sg['in_range'] = sg['_sort'].between(idx_from, idx_to)

        fs = go.Figure()

        # highlight range zone
        sems_in  = sg[sg['in_range']]['semester'].tolist()
        sems_all = sg['semester'].tolist()
        if sems_in and sem_only == 'all' and (sem_from != '1/I' or sem_to != '4/II'):
            x0 = sems_in[0]; x1 = sems_in[-1]
            fs.add_vrect(x0=x0, x1=x1, fillcolor='#6A1B9A', opacity=0.07,
                         layer='below', line_width=0)

        # เส้น GPA ทั้งหมด
        fs.add_trace(go.Scatter(
            x=sg['semester'], y=sg['gpa'],
            mode='lines+markers+text',
            text=sg['gpa'].astype(str), textposition='top center',
            textfont=dict(size=10, color='#6A1B9A'),
            line=dict(color='#6A1B9A', width=2.5, shape='spline'),
            marker=dict(
                size=[12 if r else 8 for r in sg['in_range']],
                color=['#6A1B9A' if r else 'white' for r in sg['in_range']],
                line=dict(color='#6A1B9A', width=2.5)
            ),
            showlegend=False,
            hovertemplate='<b>ພາກ %{x}</b><br>GPA: %{y}<extra></extra>'
        ))

        # highlight เฉพาะพากที่ filter
        if sem_only != 'all':
            sg_only = sg[sg['semester'] == sem_only]
            if not sg_only.empty:
                fs.add_trace(go.Scatter(
                    x=sg_only['semester'], y=sg_only['gpa'],
                    mode='markers', marker=dict(size=18, color='#E65100',
                                                 line=dict(color='white', width=3)),
                    showlegend=False, name=sem_only,
                    hovertemplate=f'<b>{sem_only}</b><br>GPA: %{{y}}<extra></extra>'
                ))

        y_vals = sg['gpa'].values
        y_range = max(y_vals) - min(y_vals) if max(y_vals) != min(y_vals) else 1.0
        pad = max(y_range * 0.4, 0.5)
        fs.update_layout(
            plot_bgcolor='#FAFBFD', paper_bgcolor=db.CARD, font=db.FONT,
            height=300, margin=dict(t=60, b=60, l=64, r=40), showlegend=False,
            hoverlabel=dict(bgcolor='white', font_size=13, bordercolor=db.BD),
            title=dict(text=f'GPA Trend — ຊ່ວງ {range_label}',
                       font=dict(size=13, color=db.TX2), x=0.01, xanchor='left')
        )
        fs.update_xaxes(showgrid=False, zeroline=False, color=db.TX,
                        title_text='ພາກຮຽນ', title_standoff=16)
        fs.update_yaxes(showgrid=True, gridcolor='#EEF0F5', zeroline=False,
                        range=[max(-0.2, min(y_vals)-pad), min(4.2, max(y_vals)+pad)],
                        title_text='GPA', title_standoff=16)

        # ── KPI ───────────────────────────────────────────────
        def mk(v, l, c):
            return html.Div(style={
                'background': db.PAGE, 'borderRadius': '10px', 'padding': '12px 14px',
                'textAlign': 'center', 'flex': '1', 'border': f'1px solid {db.BD}', 'minWidth': '80px'
            }, children=[
                html.Div(str(v), style={'fontSize': '24px', 'fontWeight': '700', 'color': c}),
                html.Div(l, style={**LAO, 'fontSize': '12px', 'color': db.TX, 'marginTop': '4px'})
            ])

        kpi_label = f'GPA ({range_label})' if sem_only == 'all' else f'GPA ({sem_only})'

        # ── ຕາຕະລາງເກຣດ ───────────────────────────────────────
        tbl = sc_show[['semester','subject_code','subject_name','grade','grade_point']].rename(columns={
            'semester':'ພາກ','subject_code':'ລະຫັດ','subject_name':'ຊື່ວິຊາ',
            'grade':'ເກຣດ','grade_point':'ຄະແນນ'
        })

        return html.Div([
            # KPI row
            html.Div(style={'display':'flex','gap':'10px','marginBottom':'14px','flexWrap':'wrap'}, children=[
                html.Div(style={
                    'background':db.PAGE,'borderRadius':'10px','padding':'12px 14px',
                    'flex':'2','border':f'1px solid {db.BD}','minWidth':'150px'
                }, children=[
                    html.Div(code, style={**LAO,'fontSize':'17px','fontWeight':'700','color':db.TX2}),
                    html.Div(f'{gen_v} · {major_v}', style={**LAO,'fontSize':'14px','fontWeight':'600','color':db.TX2,'marginTop':'4px'}),
                    html.Div(style={'marginTop':'6px'}, children=[
                        html.Span(f'ກຸ່ມ {cl_v}', style={
                            **LAO,
                            'background':f'{cl_c}15','color':cl_c,
                            'padding':'2px 10px','borderRadius':'20px',
                            'fontSize':'13px','fontWeight':'700',
                            'border':f'1px solid {cl_c}30'
                        })
                    ])
                ]),
                mk(str(gpa_all),    'GPA ລວມທຸກພາກ', '#6A1B9A'),
                mk(str(gpa_range),  kpi_label,        '#E65100'),
                mk(str(n_subj),     'ວິຊາ (range)',    db.BLUE),
                mk(str(ac),         'ເກຣດ A',          db.GREEN),
                mk(str(fc),         'ເກຣດ F',          db.RED),
            ]),

            # GPA Trend
            dcc.Graph(figure=fs, config={'displayModeBar': False}),

            # ຕາຕະລາງ + Export
            html.Div(style={'display':'flex','justifyContent':'space-between',
                            'alignItems':'center','margin':'14px 0 10px'}, children=[
                html.Div(style={'display':'flex','alignItems':'center','gap':'8px'}, children=[
                    html.Div(style={'width':'3px','height':'16px','background':'#6A1B9A','borderRadius':'2px'}),
                    html.Div(f'ຕາຕະລາງເກຣດ — {range_label} ({n_subj} ວິຊາ)',
                             style={**LAO,'fontSize':'13px','fontWeight':'600','color':db.TX2})
                ]),
                html.A(
                    html.Button('⬇ Export Excel', style={
                        'padding':'7px 16px','background':db.GREEN,'color':'white',
                        'border':'none','borderRadius':'8px','fontSize':'12px',
                        'fontWeight':'600','cursor':'pointer',
                        'fontFamily':'Noto Sans Lao,Segoe UI,Arial,sans-serif'
                    }),
                    href=f'/export/{code}', target='_blank', style={'textDecoration':'none'}
                )
            ]),
            dash_table.DataTable(
                data=tbl.to_dict('records'),
                columns=[{'name': c, 'id': c} for c in tbl.columns],
                style_table={'overflowX':'auto','borderRadius':'10px','overflow':'hidden',
                             'border':f'1px solid {db.BD}'},
                style_header={
                    'backgroundColor':'#F8FAFD','color':db.TX,'fontWeight':'600',
                    'fontSize':'12px','border':'none','padding':'12px 16px',
                    'borderBottom':f'1px solid {db.BD}',
                    'fontFamily':'Noto Sans Lao,Segoe UI,Arial,sans-serif'
                },
                style_cell={
                    'fontSize':'13px','padding':'10px 16px','border':'none',
                    'borderBottom':f'1px solid {db.BD}','textAlign':'center',
                    'fontFamily':'Noto Sans Lao,Segoe UI,Arial,sans-serif',
                    'color':db.TX2,'backgroundColor':'white'
                },
                style_data={'backgroundColor':'white'},
                style_data_conditional=[
                    {'if':{'row_index':'odd'},'backgroundColor':'#FAFBFD'},
                    {'if':{'filter_query':'{ເກຣດ} = "F"'},
                     'backgroundColor':'#FFEBEE','color':'#B71C1C','fontWeight':'700'},
                    {'if':{'filter_query':'{ເກຣດ} = "A"'},
                     'backgroundColor':'#E8F5E9','color':'#1B5E20','fontWeight':'700'},
                    {'if':{'filter_query':'{ເກຣດ} = "B+"'},
                     'backgroundColor':'#E3F2FD','color':'#0D47A1','fontWeight':'600'},  
                ],
                page_size=15, sort_action='native', style_as_list_view=True,
            )
        ])