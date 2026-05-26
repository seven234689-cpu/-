from dash import html, dcc, Input, Output, dash_table
import plotly.graph_objects as go
import db

student_opts = [
    {'label': f"{r['student_code']}  ·  {'ຊາຍ' if r['gender']=='M' else 'ຍິງ'}",
     'value': r['student_code']}
    for _, r in db.df_student.sort_values('student_code').iterrows()
]

LAO = {'fontFamily': 'Noto Sans Lao,Segoe UI,Arial,sans-serif'}

layout = html.Div(style={'padding': '28px 32px', 'background': db.PAGE, 'minHeight': '100vh'}, children=[
    html.Div(style={'marginBottom': '24px'}, children=[
        html.Div('ຄົ້ນຫານັກສຶກສາ', style={'fontSize': '22px', 'fontWeight': '700', 'color': db.TX2}),
        html.Div('ເລືອກລະຫັດ ເພື່ອເບິ່ງ GPA Trend ແລະ ເກຣດທຸກວິຊາ',
                 style={'fontSize': '13px', 'color': db.TX, 'marginTop': '4px',
                        'fontFamily': 'Noto Sans Lao,Segoe UI,Arial,sans-serif'}),
    ]),
    html.Div(style=db.card_style('#6A1B9A'), children=[
        db.sec_title('ຄົ້ນຫາ'),
        db.sec_sub('ພິມ ຫຼື ເລືອກລະຫັດນ.ສ ຈາກລາຍການ'),
        dcc.Dropdown(
            id='search-dd',
            options=student_opts,
            placeholder='ຄົ້ນຫາ... ເຊັ່ນ 205N0064',
            searchable=True,
            clearable=True,
            style={'fontSize': '13px'}
        ),
        html.Div(id='search-result', style={'marginTop': '20px'})
    ]),
])


def register_callbacks(app):

    @app.callback(Output('search-result', 'children'), Input('search-dd', 'value'))
    def show(code):
        if not code:
            return html.Div(style={
                'textAlign': 'center', 'padding': '36px',
                'border': f'1.5px dashed {db.BD}', 'borderRadius': '12px',
                'background': db.PAGE
            }, children=[
                html.Div('ເລືອກນ.ສ ດ້ານເທິງ ເພື່ອເບິ່ງຂໍ້ມູນ',
                         style={**LAO, 'color': '#90A4AE', 'fontSize': '13px', 'fontWeight': '500'}),
            ])

        stu = db.df_gpa[db.df_gpa['student_code'] == code]
        if stu.empty:
            return html.Div('ບໍ່ພົບຂໍ້ມູນ', style={**LAO, 'color': db.RED})

        gpa_v = stu.iloc[0]['gpa']
        gen_v = 'ຊາຍ' if stu.iloc[0]['gender'] == 'M' else 'ຍິງ'
        cl_v  = stu.iloc[0]['cluster']
        cl_c  = db.CC.get(cl_v, '#546078')

        sem_idx_map = {s:i for i,s in enumerate(db.sem_order)}
        sc = db.df[db.df['student_code'] == code][
            ['semester', 'sem_order', 'subject_code', 'subject_name', 'grade', 'grade_point']
        ].copy()
        sc['_sort'] = sc['semester'].map(sem_idx_map)
        sc = sc.sort_values('_sort').drop(columns=['_sort'])

        tbl = sc[['semester', 'subject_code', 'subject_name', 'grade', 'grade_point']].rename(columns={
            'semester': 'ພາກ', 'subject_code': 'ລະຫັດ', 'subject_name': 'ຊື່ວິຊາ',
            'grade': 'ເກຣດ', 'grade_point': 'ຄະແນນ'
        })

        sg = (sc.groupby(['semester', 'sem_order'])['grade_point']
                .mean().reset_index(name='gpa').sort_values('sem_order'))
        sg['gpa'] = sg['gpa'].round(2)
        fc = int((sc['grade'] == 'F').sum())
        ac = int((sc['grade'] == 'A').sum())

        fs = go.Figure()
        fs.add_trace(go.Scatter(
            x=sg['semester'], y=sg['gpa'],
            mode='lines+markers+text',
            text=sg['gpa'].astype(str), textposition='top center',
            textfont=dict(size=10, color='#6A1B9A'),
            line=dict(color='#6A1B9A', width=2.5, shape='spline'),
            marker=dict(size=9, color='white', line=dict(color='#6A1B9A', width=2.5)),
            fill=None,
            showlegend=False,
            hovertemplate='<b>ພາກ %{x}</b><br>GPA: %{y}<extra></extra>'
        ))
        # คำนวณ Y range ให้มี padding รอบด้านสมดุล
        y_vals = sg['gpa'].values
        y_range = max(y_vals) - min(y_vals) if max(y_vals) != min(y_vals) else 1.0
        pad = max(y_range * 0.4, 0.5)
        y_min = max(-0.2, min(y_vals) - pad)
        y_max = min(4.2, max(y_vals) + pad)
        fs.update_layout(
            plot_bgcolor='#FAFBFD', paper_bgcolor=db.CARD, font=db.FONT,
            height=300, margin=dict(t=60, b=60, l=64, r=40), showlegend=False,
            hoverlabel=dict(bgcolor='white', font_size=13, bordercolor=db.BD))
        fs.update_xaxes(showgrid=False, zeroline=False, color=db.TX,
                        title_text='ພາກຮຽນ', title_standoff=16,
                        ticklen=6, ticks='outside')
        fs.update_yaxes(showgrid=True, gridcolor='#EEF0F5', zeroline=False,
                        range=[y_min, y_max], title_text='GPA',
                        title_standoff=16, ticklen=6, ticks='outside')

        def mk(v, l, c):
            return html.Div(style={
                'background': db.PAGE, 'borderRadius': '10px', 'padding': '12px 14px',
                'textAlign': 'center', 'flex': '1', 'border': f'1px solid {db.BD}', 'minWidth': '80px'
            }, children=[
                html.Div(str(v), style={'fontSize': '20px', 'fontWeight': '700', 'color': c}),
                html.Div(l, style={**LAO, 'fontSize': '10px', 'color': db.TX, 'marginTop': '4px'})
            ])

        return html.Div([
            html.Div(style={'display': 'flex', 'gap': '10px', 'marginBottom': '14px', 'flexWrap': 'wrap'}, children=[
                html.Div(style={
                    'background': db.PAGE, 'borderRadius': '10px', 'padding': '12px 14px',
                    'flex': '2', 'border': f'1px solid {db.BD}', 'minWidth': '150px'
                }, children=[
                    html.Div(code, style={**LAO, 'fontSize': '13px', 'fontWeight': '700', 'color': db.TX2}),
                    html.Div(gen_v, style={**LAO, 'fontSize': '11px', 'color': db.TX, 'marginTop': '2px'}),
                    html.Div(style={'marginTop': '6px'}, children=[
                        html.Span(f'ກຸ່ມ {cl_v}', style={
                            **LAO,
                            'background': f'{cl_c}15', 'color': cl_c,
                            'padding': '2px 10px', 'borderRadius': '20px',
                            'fontSize': '11px', 'fontWeight': '600',
                            'border': f'1px solid {cl_c}30'
                        })
                    ])
                ]),
                mk(str(gpa_v), 'GPA ລວມ',      '#6A1B9A'),
                mk(str(len(sc)), 'ວິຊາທັງໝົດ', db.BLUE),
                mk(str(ac),    'ເກຣດ A',       db.GREEN),
                mk(str(fc),    'ເກຣດ F',       db.RED),
            ]),
            dcc.Graph(figure=fs, config={'displayModeBar': False}),

            # Gender comparison
            html.Div(style=db.card_style('#1565C0'), children=[
                db.sec_title('ປຽບທຽບ GPA ກັບຄ່າສະເລ່ຍ'),
                db.sec_sub(f'GPA ຂອງ {code} ທຽບກັບຄ່າສະເລ່ຍ GPA ຊາຍ/ຍິງ ທັງໝົດ'),
                dcc.Graph(
                    figure=go.Figure(data=[
                        go.Bar(name=f'{"ຊາຍ" if stu.iloc[0]["gender"]=="M" else "ຍິງ"} ສະເລ່ຍ',
                               x=['ຄ່າສະເລ່ຍ GPA'],
                               y=[round(db.df_gpa[db.df_gpa['gender']==stu.iloc[0]['gender']]['gpa'].mean(), 3)],
                               marker_color='#1976D2', marker_line_width=0),
                        go.Bar(name='ສະເລ່ຍທຸກຄົນ',
                               x=['ຄ່າສະເລ່ຍ GPA'],
                               y=[db.avgGPA],
                               marker_color='#4A148C', marker_line_width=0),
                        go.Bar(name=f'{code}',
                               x=['ຄ່າສະເລ່ຍ GPA'],
                               y=[float(gpa_v)],
                               marker_color='#2E7D32' if cl_v=='ສູງ' else ('#1565C0' if cl_v=='ກາງ' else '#C62828'),
                               marker_line_width=0),
                    ]).update_layout(
                        plot_bgcolor='#FAFBFD', paper_bgcolor=db.CARD, font=db.FONT,
                        height=280, barmode='group', bargap=0.35, bargroupgap=0.1,
                        margin=dict(t=48,b=56,l=64,r=40),
                        showlegend=True,
                        legend=dict(orientation='h', y=1.12, x=0, bgcolor='rgba(0,0,0,0)',
                                    font=dict(size=12, color='#000000')),
                        hoverlabel=dict(bgcolor='white', font_size=13, bordercolor=db.BD)
                    ).update_xaxes(showgrid=False, zeroline=False, color=db.TX
                    ).update_yaxes(showgrid=True, gridcolor='#EEF0F5', zeroline=False,
                                   range=[0, 4.3], title_text='GPA'),
                    config={'displayModeBar': False}
                ),
                # stat boxes
                html.Div(style={'display':'flex','gap':'10px','marginTop':'10px','flexWrap':'wrap'}, children=[
                    html.Div(style={'background':db.PAGE,'borderRadius':'10px','padding':'12px',
                                    'textAlign':'center','flex':'1','border':f'1px solid {db.BD}'}, children=[
                        html.Div(str(gpa_v), style={'fontSize':'20px','fontWeight':'700','color':'#1565C0'}),
                        html.Div(f'GPA {code}', style={**LAO,'fontSize':'10px','color':db.TX,'marginTop':'3px'})
                    ]),
                    html.Div(style={'background':db.PAGE,'borderRadius':'10px','padding':'12px',
                                    'textAlign':'center','flex':'1','border':f'1px solid {db.BD}'}, children=[
                        html.Div(str(round(db.df_gpa[db.df_gpa['gender']==stu.iloc[0]['gender']]['gpa'].mean(),3)),
                                 style={'fontSize':'20px','fontWeight':'700','color':'#1565C0'}),
                        html.Div(f'ສະເລ່ຍ{"ຊາຍ" if stu.iloc[0]["gender"]=="M" else "ຍິງ"}',
                                 style={**LAO,'fontSize':'10px','color':db.TX,'marginTop':'3px'})
                    ]),
                    html.Div(style={'background':db.PAGE,'borderRadius':'10px','padding':'12px',
                                    'textAlign':'center','flex':'1','border':f'1px solid {db.BD}'}, children=[
                        html.Div(str(db.avgGPA), style={'fontSize':'20px','fontWeight':'700','color':'#6A1B9A'}),
                        html.Div('ສະເລ່ຍທຸກຄົນ', style={**LAO,'fontSize':'10px','color':db.TX,'marginTop':'3px'})
                    ]),
                    html.Div(style={'background':db.PAGE,'borderRadius':'10px','padding':'12px',
                                    'textAlign':'center','flex':'1',
                                    'border':f'1px solid {"#2E7D32" if float(gpa_v) >= db.avgGPA else "#C62828"}'}, children=[
                        html.Div('ສູງກວ່າສະເລ່ຍ' if float(gpa_v) >= db.avgGPA else 'ຕ່ຳກວ່າສະເລ່ຍ',
                                 style={'fontSize':'13px','fontWeight':'700',
                                        'color':'#2E7D32' if float(gpa_v) >= db.avgGPA else '#C62828'}),
                        html.Div(f'{round(abs(float(gpa_v)-db.avgGPA),3)} GPA',
                                 style={**LAO,'fontSize':'10px','color':db.TX,'marginTop':'3px'})
                    ]),
                ])
            ]),
            html.Div(style={'display':'flex','justifyContent':'space-between',
                            'alignItems':'center','margin':'14px 0 10px'}, children=[
                html.Div(style={'display':'flex','alignItems':'center','gap':'8px'}, children=[
                    html.Div(style={'width':'3px','height':'16px','background':'#6A1B9A','borderRadius':'2px'}),
                    html.Div('ຕາຕະລາງເກຣດທຸກວິຊາ',
                             style={**LAO,'fontSize':'13px','fontWeight':'600','color':db.TX2})
                ]),
                html.A(
                    html.Button('⬇ Export Excel', style={
                        'padding':'7px 16px','background':db.GREEN,'color':'white',
                        'border':'none','borderRadius':'8px','fontSize':'12px',
                        'fontWeight':'600','cursor':'pointer',
                        'fontFamily':'Noto Sans Lao,Segoe UI,Arial,sans-serif'
                    }),
                    href=f'/export/{code}',
                    target='_blank',
                    style={'textDecoration':'none'}
                )
            ]),
            dash_table.DataTable(
                data=tbl.to_dict('records'),
                columns=[{'name': c, 'id': c} for c in tbl.columns],
                style_table={'overflowX': 'auto', 'borderRadius': '10px', 'overflow': 'hidden',
                             'border': f'1px solid {db.BD}'},
                style_header={
                    'backgroundColor': '#F8FAFD', 'color': db.TX, 'fontWeight': '600',
                    'fontSize': '12px', 'border': 'none', 'padding': '12px 16px',
                    'borderBottom': f'1px solid {db.BD}',
                    'fontFamily': 'Noto Sans Lao,Segoe UI,Arial,sans-serif'
                },
                style_cell={
                    'fontSize': '13px', 'padding': '10px 16px', 'border': 'none',
                    'borderBottom': f'1px solid {db.BD}', 'textAlign': 'center',
                    'fontFamily': 'Noto Sans Lao,Segoe UI,Arial,sans-serif',
                    'color': db.TX2, 'backgroundColor': 'white'
                },
                style_data={'backgroundColor': 'white'},
                style_data_conditional=[
                    {'if': {'row_index': 'odd'}, 'backgroundColor': '#FAFBFD'},
                    {'if': {'filter_query': '{ເກຣດ} = "F"'},
                     'backgroundColor': '#FFEBEE', 'color': '#B71C1C', 'fontWeight': '700'},
                    {'if': {'filter_query': '{ເກຣດ} = "A"'},
                     'backgroundColor': '#E8F5E9', 'color': '#1B5E20', 'fontWeight': '700'},
                    {'if': {'filter_query': '{ເກຣດ} = "B+"'},
                     'backgroundColor': '#E3F2FD', 'color': '#0D47A1', 'fontWeight': '600'},
                ],
                page_size=15, sort_action='native', style_as_list_view=True,
            )
        ])