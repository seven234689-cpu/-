from dash import html, dcc, Input, Output, callback
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import db

# ── Chart helpers ──────────────────────────────────────────
def B(h=300, leg=False):
    return dict(plot_bgcolor='#FAFBFD', paper_bgcolor=db.CARD, font=db.FONT,
        height=h, margin=dict(t=24,b=48,l=56,r=24), showlegend=leg,
        legend=dict(orientation='h',y=1.08,x=0,bgcolor='rgba(0,0,0,0)',
                    font=dict(size=12,color=db.TX2)),
        hoverlabel=dict(bgcolor='white',font_size=13,font_color='#1E2A3A',bordercolor='#1E2A3A',font_family='Noto Sans Lao,Segoe UI,Arial,sans-serif'))

def xax(): return dict(showgrid=False,zeroline=False,color=db.TX,linecolor=db.BD,linewidth=1)
def yax(): return dict(showgrid=True,gridcolor='#EEF0F5',zeroline=False,color=db.TX,linecolor=db.BD)

# ── Static figures (all data) ─────────────────────────────
# Donut cluster
fig_donut = go.Figure(go.Pie(
    labels=['ກຸ່ມ ສູງ', 'ກຸ່ມ ກາງ', 'ກຸ່ມ ສ່ຽງ'],
    values=[db.high, db.mid, db.risk], hole=0.55,
    marker=dict(colors=['#2E7D32','#1565C0','#C62828'], line=dict(color='white',width=3)),
    textinfo='none',
    hovertemplate='<b>%{label}</b><br>%{value} ຄົນ<br>%{percent}<extra></extra>'
))
fig_donut.update_layout(
    plot_bgcolor=db.CARD, paper_bgcolor=db.CARD, font=db.FONT,
    height=320, margin=dict(t=20,b=20,l=20,r=20), showlegend=True,
    legend=dict(
        orientation='h', x=0.5, y=-0.15, xanchor='center',
        font=dict(size=12, color=db.TX2),
        bgcolor='rgba(0,0,0,0)'
    ),
    hoverlabel=dict(bgcolor='white',font_size=13,font_color='#1E2A3A',bordercolor='#1E2A3A',font_family='Noto Sans Lao,Segoe UI,Arial,sans-serif'),
    annotations=[dict(
        text=f'<b>{db.total}</b><br>ນ.ສ ທັງໝົດ',
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=16, color=db.TX2,
                  family='Noto Sans Lao,Segoe UI')
    )]
)

# Grade dist
gc = ['#1B5E20','#2E7D32','#66BB6A','#F57F17','#FBC02D','#EF9A9A','#EF5350','#B71C1C']
fig_grade = go.Figure()
for i,(_,row) in enumerate(db.gd.iterrows()):
    fig_grade.add_trace(go.Bar(
        x=[row['grade']], y=[row['count']],
        marker_color=gc[i], marker_line_width=0,
        text=str(int(row['count'])), textposition='outside',
        textfont=dict(color=db.TX,size=11), name=row['grade'],
        hovertemplate=f"ເກຣດ <b>{row['grade']}</b>: {int(row['count'])} ຄັ້ງ<extra></extra>"
    ))
fig_grade.update_layout(**B(280), bargap=0.3)
fig_grade.update_xaxes(**xax(), title_text='ເກຣດ')
fig_grade.update_yaxes(**yax(), title_text='ຈຳນວນ')

# Heatmap
if len(db.hp) > 0:
    fig_heat = px.imshow(db.hp, color_continuous_scale='YlOrRd', aspect='auto',
        labels=dict(x='ພາກຮຽນ', y='ລະຫັດວິຊາ', color='GP'))
    fig_heat.update_coloraxes(colorbar=dict(
        tickfont=dict(color=db.TX), title=dict(text='GP', font=dict(color=db.TX))))
    fig_heat.update_layout(
        plot_bgcolor=db.CARD, paper_bgcolor=db.CARD, font=db.FONT,
        height=1000, margin=dict(t=24,b=48,l=120,r=20))
    fig_heat.update_xaxes(color=db.TX, linecolor=db.BD)
    fig_heat.update_yaxes(color=db.TX, linecolor=db.BD)
else:
    fig_heat = go.Figure()
    fig_heat.update_layout(plot_bgcolor=db.CARD, paper_bgcolor=db.CARD,
        height=200, annotations=[dict(text='ບໍ່ມີຂໍ້ມູນ', x=0.5, y=0.5,
        showarrow=False, font=dict(size=16, color=db.TX))])



# Box plot
fig_box = go.Figure()
for sem in db.sem_order:
    d = db.df[db.df['semester']==sem].groupby('student_code')['grade_point'].mean()
    if len(d)==0: continue
    fig_box.add_trace(go.Box(
        y=d.values, name=sem, marker_color=db.BLUE,
        line=dict(color=db.BLUE,width=1.5), fillcolor='rgba(21,101,192,0.08)',
        hovertemplate=f'<b>ພາກ {sem}</b><br>GPA: %{{y:.2f}}<extra></extra>'
    ))
fig_box.update_layout(**B(300))
fig_box.update_xaxes(**xax(), title_text='ພາກຮຽນ')
fig_box.update_yaxes(**yax(), title_text='GPA')

# Correlation
if len(db.df) > 0:
    pivot_c = (db.df.groupby(['student_code','subject_code'])['grade_point']
                 .mean().unstack(fill_value=np.nan))
    pivot_c = pivot_c.loc[:, pivot_c.count() >= 30]
    corr_m  = pivot_c.corr()
    fig_corr = px.imshow(corr_m, color_continuous_scale='RdBu_r', zmin=-1, zmax=1,
        aspect='auto', labels=dict(color='r'))
    fig_corr.update_coloraxes(colorbar=dict(
        tickfont=dict(color=db.TX), title=dict(text='r',font=dict(color=db.TX))))
    fig_corr.update_layout(
        plot_bgcolor=db.CARD, paper_bgcolor=db.CARD, font=db.FONT,
        height=600, margin=dict(t=24,b=48,l=100,r=20))
    fig_corr.update_xaxes(color=db.TX, linecolor=db.BD, tickfont=dict(size=8))
    fig_corr.update_yaxes(color=db.TX, linecolor=db.BD, tickfont=dict(size=8))
else:
    fig_corr = go.Figure()
    fig_corr.update_layout(plot_bgcolor=db.CARD, paper_bgcolor=db.CARD,
        height=200, annotations=[dict(text='ບໍ່ມີຂໍ້ມູນ', x=0.5, y=0.5,
        showarrow=False, font=dict(size=16, color=db.TX))])

# ── Helpers ───────────────────────────────────────────────
def card(title, sub, children, accent=db.BLUE):
    return html.Div(style=db.card_style(accent), children=[
        db.sec_title(title), db.sec_sub(sub), *children])

def stat_box(value, label, color):
    return html.Div(style={
        'background':db.PAGE,'borderRadius':'10px','padding':'14px 16px',
        'textAlign':'center','flex':'1','border':f'1px solid {db.BD}'
    }, children=[
        html.Div(str(value), style={'fontSize':'22px','fontWeight':'700','color':color}),
        html.Div(label, style={'fontSize':'11px','color':db.TX,'marginTop':'4px',
                               'fontFamily':'Noto Sans Lao,Segoe UI,Arial,sans-serif'})
    ])

# Semester options for filter
sem_options = [{'label':'ທຸກພາກ','value':'all'}] + \
              [{'label':s,'value':s} for s in db.sem_order]

major_options = [
    {'label':'ທຸກສາຂາ',                           'value':'all'},
    {'label':'ວິທະຍາສາດຄອມພິວເຕີ',               'value':'ວິທະຍາສາດຄອມພິວເຕີ'},
    {'label':'ການພັດທະນາເວັບໄຊ',                 'value':'ການພັດທະນາເວັບໄຊ'},
    {'label':'ການພັດທະນາໂປຣແກຣມຄອມພິວເຕີ',      'value':'ການພັດທະນາໂປຣແກຣມຄອມພິວເຕີ'},
]

# ── Layout ────────────────────────────────────────────────
def layout():
    return html.Div(style={'padding':'28px 32px','background':db.PAGE,'minHeight':'100vh'}, children=[

    html.Div(style={'marginBottom':'24px','display':'flex',
                    'justifyContent':'space-between','alignItems':'center'}, children=[
        html.Div([
            html.Div('Dashboard', style={'fontSize':'22px','fontWeight':'700','color':db.TX2}),
            html.Div('ພາບລວມຜົນການຮຽນ — ພາກວິຊາວິທະຍາສາດຄອມພິວເຕີ',
                     style={'fontSize':'13px','color':db.TX,'marginTop':'4px',
                            'fontFamily':'Noto Sans Lao,Segoe UI,Arial,sans-serif'}),
        ]),
        dcc.Dropdown(id='dash-major-filter', options=major_options,
            value='all', clearable=False,
            persistence=True, persistence_type='memory',
            style={'fontSize':'13px','minWidth':'200px'})
    ]),


    # KPI row
    html.Div(className='kpi-row', style={'display':'flex','gap':'12px','marginBottom':'22px','flexWrap':'wrap'}, children=[
        db.kpi_card(db.total,       'ນ.ສ ທັງໝົດ',   db.BLUE,   '/assets/grad.png'),
        db.kpi_card(db.total_subj,  'ວິຊາທັງໝົດ',   '#546078', '/assets/book.png'),
        db.kpi_card(db.avgGPA,      'GPA ສະເລ່ຍ',   db.BLUE,   '/assets/chart.png'),
        db.kpi_card(db.high,        'ກຸ່ມ ສູງ',       db.GREEN,  '/assets/trophy.png'),
        db.kpi_card(db.mid,         'ກຸ່ມ ກາງ',       db.BLUE,   '/assets/bar.png'),
        db.kpi_card(db.risk,        'ກຸ່ມ ສ່ຽງ',      db.RED,    '/assets/warning.png'),
        db.kpi_card(f'{db.frate}%', 'ອັດຕາ F',       db.RED,    '/assets/close.png'),
        db.kpi_card(db.male,        'ນ.ສ ຊາຍ',       db.BLUE,   '/assets/male.png'),
        db.kpi_card(db.female,      'ນ.ສ ຍິງ',       '#6A1B9A', '/assets/female.png'),
    ]),

    # Grade + Cluster
    html.Div(className='grid-2col', children=[
        html.Div(style=db.card_style(db.BLUE), children=[
            db.sec_title('ການກະຈາຍຂອງເກຣດ'),
            db.sec_sub('ຈຳນວນນ.ສ ທີ່ໄດ້ເກຣດແຕ່ລະລະດັບ'),
            dcc.Graph(id='dash-grade', config={'displayModeBar':False},
                      style={'height':'300px'}, responsive=True)
        ]),
        card('ການຈັດກຸ່ມ (K-Means)','ແບ່ງ 3 ກຸ່ມ: ສູງ / ກາງ / ສ່ຽງ',
             [
                 dcc.Graph(id='dash-donut', config={'displayModeBar':False},
                           style={'height':'320px'}, responsive=True),
                 html.Div(id='dash-cluster-stats', style={'display':'flex','gap':'8px','marginTop':'8px','flexWrap':'wrap'})
             ], accent=db.GREEN),
    ]),

    # Trend + Gender
    html.Div(className='grid-2col', children=[
        html.Div(style=db.card_style(db.BLUE), children=[
            db.sec_title('ແນວໂນ້ມ GPA ລາຍພາກ'),
            db.sec_sub('GPA ສະເລ່ຍຂອງນ.ສ ທຸກຄົນ ຕາມພາກຮຽນ'),
            dcc.Graph(id='dash-trend', config={'displayModeBar':False},
                      style={'height':'300px'}, responsive=True)
        ]),
        html.Div(style=db.card_style('#6A1B9A'), children=[
            db.sec_title('GPA ປຽບທຽບ ຊາຍ vs ຍິງ'),
            db.sec_sub('ທ່ວງໂນ້ມ GPA ແຍກຕາມເພດ'),
            dcc.Graph(id='dash-gender', config={'displayModeBar':False},
                      style={'height':'300px'}, responsive=True)
        ]),
    ]),

    html.Div(className='grid-2col', children=[
        card('🔴 Top 10 ວິຊາທີ່ຍາກທີ່ສຸດ',
             'ວິຊາທີ່ ນ.ສ ໄດ້ຄະແນນສະເລ່ຍຕ່ຳທີ່ສຸດ 10 ວິຊາ',
             [dcc.Graph(id='dash-hard', config={'displayModeBar':False},
                        style={'height':'340px'}, responsive=True)], accent=db.RED),
        card('🟢 Top 10 ວິຊາທີ່ງ່າຍທີ່ສຸດ',
             'ວິຊາທີ່ນ.ສ ໄດ້ຄະແນນສະເລ່ຍສູງທີ່ສຸດ 10 ວິຊາ',
             [dcc.Graph(id='dash-easy', config={'displayModeBar':False},
                        style={'height':'340px'}, responsive=True)], accent=db.GREEN),
    ]),

    # Scatter Plot
    card('ການກະຈາຍ GPA ລາຍຄົນ (Scatter Plot)',
         'ແຕ່ລະຈຸດ = ນ.ສ 1 ຄົນ · ສີຂຽວ = ສູງ · ສີຟ້າ = ກາງ · ສີແດງ = ສ່ຽງ',
         [dcc.Graph(id='dash-scatter', config={'displayModeBar':False},
                    style={'height':'380px'}, responsive=True)], accent='#0277BD'),

])


# ── Callbacks ─────────────────────────────────────────────
def register_callbacks(app):

    @app.callback(
        Output('dash-trend','figure'),
        Output('dash-gender','figure'),
        Output('dash-grade','figure'),
        Output('dash-scatter','figure'),
        Output('dash-donut','figure'),
        Output('dash-cluster-stats','children'),
        Output('dash-hard','figure'),
        Output('dash-easy','figure'),
        Input('dash-major-filter','value')
    )
    def update_charts(major):
        sem = 'all'
        # Filter data by major
        if major == 'all':
            dff = db.df
            dff_gpa = db.df_gpa
        else:
            if 'major' in db.df_gpa.columns:
                stu_in = db.df_gpa[db.df_gpa['major'] == major]['student_code']
            else:
                stu_in = db.df_gpa['student_code']
            dff = db.df[db.df['student_code'].isin(stu_in)]
            # คำนวณ GPA ใหม่จากข้อมูลที่ filter
            import numpy as np
            from sklearn.cluster import KMeans
            from sklearn.preprocessing import StandardScaler
            dff_gpa = (dff.groupby(['student_id','student_code','gender'])['grade_point']
                         .mean().reset_index(name='gpa'))
            dff_gpa['gpa'] = dff_gpa['gpa'].round(3)
            if len(dff_gpa) >= 3:
                sc = StandardScaler()
                X = sc.fit_transform(dff_gpa[['gpa']].values)
                km = KMeans(n_clusters=3, random_state=42, n_init=10)
                dff_gpa['cn'] = km.fit_predict(X)
                ci = np.argsort(sc.inverse_transform(km.cluster_centers_).flatten())
                lm = {ci[0]:'ສ່ຽງ', ci[1]:'ກາງ', ci[2]:'ສູງ'}
                dff_gpa['cluster'] = dff_gpa['cn'].map(lm)
            else:
                dff_gpa['cluster'] = 'ກາງ'

        # Trend
        trend = (dff.groupby(['semester','sem_order'])['grade_point']
                   .mean().reset_index(name='avg_gpa').sort_values('sem_order'))
        trend['avg_gpa'] = trend['avg_gpa'].round(3)

        ft = go.Figure()
        ft.add_trace(go.Scatter(
            x=trend['semester'], y=trend['avg_gpa'],
            mode='lines+markers+text',
            text=trend['avg_gpa'].astype(str), textposition='top center',
            textfont=dict(size=10,color=db.BLUE),
            line=dict(color=db.BLUE,width=3,shape='spline'),
            marker=dict(size=9,color='white',line=dict(color=db.BLUE,width=2.5)),
            fill='tozeroy', fillcolor='rgba(21,101,192,0.05)',
            hovertemplate='<b>ພາກ %{x}</b><br>GPA: %{y:.3f}<extra></extra>'
        ))
        ft.update_layout(**B(380))
        ft.update_xaxes(**xax(), title_text='ພາກຮຽນ', range=[-0.5, 7.5])
        ft.update_yaxes(**yax(), range=[2.0,4.0], title_text='GPA ສະເລ່ຍ')

        # Gender
        trend_g = (dff.groupby(['semester','sem_order','gender'])['grade_point']
                     .mean().reset_index(name='avg_gpa').sort_values('sem_order'))
        fg = go.Figure()
        for g,c,n,dash in [('M',db.BLUE,'ຊາຍ','solid'),('F','#6A1B9A','ຍິງ','dot')]:
            d = trend_g[trend_g['gender']==g]
            fg.add_trace(go.Scatter(
                x=d['semester'], y=d['avg_gpa'], mode='lines+markers', name=n,
                line=dict(color=c,width=2.5,shape='spline',dash=dash),
                marker=dict(size=7,color='white',line=dict(color=c,width=2.5)),
                hovertemplate=f'<b>{n}</b> ພາກ %{{x}}: %{{y:.3f}}<extra></extra>'
            ))
        fg.update_layout(**B(380,leg=True))
        fg.update_xaxes(**xax(), title_text='ພາກຮຽນ')
        fg.update_yaxes(**yax(), range=[2.0,4.0], title_text='GPA ສະເລ່ຍ')

        # Grade dist
        gd = dff['grade'].value_counts().reindex(
            ['A','B+','B','C+','C','D+','D','F']).fillna(0).reset_index()
        gd.columns = ['grade','count']
        gc2 = ['#1B5E20','#2E7D32','#66BB6A','#F57F17','#FBC02D','#EF9A9A','#EF5350','#B71C1C']
        fgd = go.Figure()
        for i,(_,row) in enumerate(gd.iterrows()):
            fgd.add_trace(go.Bar(
                x=[row['grade']], y=[row['count']],
                marker_color=gc2[i], marker_line_width=0,
                text=str(int(row['count'])), textposition='outside',
                textfont=dict(color=db.TX,size=11), name=row['grade'],
                hovertemplate=f"ເກຣດ <b>{row['grade']}</b>: {int(row['count'])}<extra></extra>"
            ))
        fgd.update_layout(
            plot_bgcolor='#FAFBFD', paper_bgcolor=db.CARD, font=db.FONT,
            height=380, margin=dict(t=40,b=56,l=64,r=64), showlegend=False,
            bargap=0.3,
            hoverlabel=dict(bgcolor='white',font_size=13,font_color='#1E2A3A',bordercolor='#1E2A3A',font_family='Noto Sans Lao,Segoe UI,Arial,sans-serif'))
        fgd.update_xaxes(**xax(), title_text='ເກຣດ')
        fgd.update_yaxes(**yax(), title_text='ຈຳນວນ',
                         range=[0, max(gd['count'].max()*1.15, 1)])

        # Scatter
        fsc = go.Figure([go.Scatter(
            x=dff_gpa[dff_gpa['cluster']==cl].index,
            y=dff_gpa[dff_gpa['cluster']==cl]['gpa'],
            mode='markers', name=cl,
            marker=dict(color=db.CC[cl], size=7, opacity=0.7,
                        line=dict(color='white', width=0.5)),
            hovertemplate='<b>%{text}</b><br>GPA: %{y:.3f}<extra></extra>',
            text=dff_gpa[dff_gpa['cluster']==cl]['student_code']
        ) for cl in ['ສູງ','ກາງ','ສ່ຽງ']])
        fsc.update_layout(
            plot_bgcolor='#FAFBFD', paper_bgcolor=db.CARD, font=db.FONT,
            height=320, margin=dict(t=24,b=48,l=56,r=24), showlegend=True,
            legend=dict(orientation='h',y=1.08,x=0,bgcolor='rgba(0,0,0,0)',
                        font=dict(size=12,color=db.TX2)),
            hoverlabel=dict(bgcolor='white',font_size=13,font_color='#1E2A3A',bordercolor='#1E2A3A',font_family='Noto Sans Lao,Segoe UI,Arial,sans-serif'))
        fsc.update_xaxes(showgrid=False,zeroline=False,color=db.TX,title_text='ລຳດັບນ.ສ')
        fsc.update_yaxes(showgrid=True,gridcolor='#EEF0F5',zeroline=False,
                         title_text='GPA',range=[0,4.2])

        # Donut
        high_n  = int((dff_gpa['cluster']=='ສູງ').sum())
        mid_n   = int((dff_gpa['cluster']=='ກາງ').sum())
        risk_n  = int((dff_gpa['cluster']=='ສ່ຽງ').sum())
        total_n = len(dff_gpa)

        fd = go.Figure(go.Pie(
            labels=['ກຸ່ມ ສູງ','ກຸ່ມ ກາງ','ກຸ່ມ ສ່ຽງ'],
            values=[high_n, mid_n, risk_n], hole=0.55,
            marker=dict(colors=['#2E7D32','#1565C0','#C62828'], line=dict(color='white',width=3)),
            textinfo='none',
            hovertemplate='<b>%{label}</b><br>%{value} ຄົນ<br>%{percent}<extra></extra>'
        ))
        fd.update_layout(
            plot_bgcolor=db.CARD, paper_bgcolor=db.CARD, font=db.FONT,
            height=320, margin=dict(t=20,b=20,l=20,r=20), showlegend=True,
            legend=dict(orientation='h', x=0.5, y=-0.15, xanchor='center',
                        font=dict(size=12, color=db.TX2), bgcolor='rgba(0,0,0,0)'),
            hoverlabel=dict(bgcolor='white',font_size=13,font_color='#1E2A3A',bordercolor='#1E2A3A',font_family='Noto Sans Lao,Segoe UI,Arial,sans-serif'),
            annotations=[dict(
                text=f'<b>{total_n}</b><br>ນ.ສ ທັງໝົດ',
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color=db.TX2, family='Noto Sans Lao,Segoe UI')
            )]
        )

        LAO = {'fontFamily':'Noto Sans Lao,Segoe UI,Arial,sans-serif'}
        cluster_stats = [
            html.Div(style={'flex':'1','textAlign':'center','background':'#E8F5E9',
                            'borderRadius':'10px','padding':'10px','border':'1px solid #A5D6A7'}, children=[
                html.Div(str(high_n), style={'fontSize':'22px','fontWeight':'700','color':'#2E7D32'}),
                html.Div('ກຸ່ມ ສູງ', style={**LAO,'fontSize':'11px','color':'#2E7D32'})
            ]),
            html.Div(style={'flex':'1','textAlign':'center','background':'#E3F2FD',
                            'borderRadius':'10px','padding':'10px','border':'1px solid #90CAF9'}, children=[
                html.Div(str(mid_n), style={'fontSize':'22px','fontWeight':'700','color':'#1565C0'}),
                html.Div('ກຸ່ມ ກາງ', style={**LAO,'fontSize':'11px','color':'#1565C0'})
            ]),
            html.Div(style={'flex':'1','textAlign':'center','background':'#FFEBEE',
                            'borderRadius':'10px','padding':'10px','border':'1px solid #FFCDD2'}, children=[
                html.Div(str(risk_n), style={'fontSize':'22px','fontWeight':'700','color':'#C62828'}),
                html.Div('ກຸ່ມ ສ່ຽງ', style={**LAO,'fontSize':'11px','color':'#C62828'})
            ]),
        ]

        # Top 10 hardest / easiest subjects (filtered by major)
        subj_avg_f = (dff.groupby(['subject_code','subject_name'])['grade_point']
                        .mean().reset_index(name='avg_gp').sort_values('avg_gp'))
        subj_avg_f['avg_gp'] = subj_avg_f['avg_gp'].round(3)
        subj_avg_f['label'] = subj_avg_f['subject_code'] + '   ' + subj_avg_f['subject_name'].str[:28]

        top_hard_f = subj_avg_f.head(10).copy()
        top_hard_f['label'] = top_hard_f['label'].str[:30]
        top_easy_f = subj_avg_f.tail(10).sort_values('avg_gp', ascending=True).copy()
        top_easy_f['label'] = top_easy_f['label'].str[:30]

        fh = go.Figure()
        fh.add_trace(go.Bar(
            x=top_hard_f['avg_gp'], y=top_hard_f['label'], orientation='h',
            marker_color='#C62828', marker_line_width=0,
            text=top_hard_f['avg_gp'].round(2), textposition='outside',
            textfont=dict(size=11, color=db.TX),
            hovertemplate='<b>%{y}</b><br>GP: %{x:.3f}<extra></extra>'
        ))
        fh.update_layout(
            plot_bgcolor='#FAFBFD', paper_bgcolor=db.CARD, font=db.FONT,
            height=400, margin=dict(t=24,b=48,l=220,r=60),
            hoverlabel=dict(bgcolor='white',font_size=13,font_color='#1E2A3A',bordercolor='#1E2A3A',font_family='Noto Sans Lao,Segoe UI,Arial,sans-serif'))
        fh.update_xaxes(**yax(), title_text='Avg Grade Point', range=[0, 4.5])
        fh.update_yaxes(**xax(), title_text='', tickfont=dict(size=11))

        fe = go.Figure()
        fe.add_trace(go.Bar(
            x=top_easy_f['avg_gp'], y=top_easy_f['label'], orientation='h',
            marker_color='#2E7D32', marker_line_width=0,
            text=top_easy_f['avg_gp'].round(2), textposition='outside',
            textfont=dict(size=11, color=db.TX),
            hovertemplate='<b>%{y}</b><br>GP: %{x:.3f}<extra></extra>'
        ))
        fe.update_layout(
            plot_bgcolor='#FAFBFD', paper_bgcolor=db.CARD, font=db.FONT,
            height=400, margin=dict(t=24,b=48,l=220,r=60),
            hoverlabel=dict(bgcolor='white',font_size=13,font_color='#1E2A3A',bordercolor='#1E2A3A',font_family='Noto Sans Lao,Segoe UI,Arial,sans-serif'))
        fe.update_xaxes(**yax(), title_text='Avg Grade Point', range=[0, 4.5])
        fe.update_yaxes(**xax(), title_text='', tickfont=dict(size=11))

        return ft, fg, fgd, fsc, fd, cluster_stats, fh, fe