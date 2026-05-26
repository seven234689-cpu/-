from dash import Dash, dcc, html, Input, Output
import db

app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server
app.title = "ລະບົບວິເຄາະຜົນການຮຽນ CS"

NAV = [
    {'href':'/',        'label':'Dashboard'},
    {'href':'/search',  'label':'ຄົ້ນຫານັກສຶກສາ'},
    {'href':'/predict', 'label':'ທຳນາຍ GPA'},
    {'href':'/admin',   'label':'Admin'},
]

def sidebar(active):
    items = []
    for nav in NAV:
        is_a = nav['href'] == active
        items.append(dcc.Link(
            html.Div(style={
                'display':'flex','alignItems':'center','gap':'10px',
                'padding':'10px 16px','borderRadius':'8px','cursor':'pointer',
                'background':'#EEF3FB' if is_a else 'transparent',
                'margin':'2px 8px',
            }, children=[
                html.Span(nav['label'], style={
                    'fontSize':'13px',
                    'fontWeight':'600' if is_a else '400',
                    'color':db.BLUE if is_a else db.TX,
                    'fontFamily':'Noto Sans Lao,Segoe UI,Arial,sans-serif'
                })
            ]),
            href=nav['href'], style={'textDecoration':'none'}
        ))

    return html.Div(style={
        'width':'200px','minHeight':'100vh',
        'background':'white',
        'borderRight':f'1px solid {db.BD}',
        'display':'flex','flexDirection':'column',
        'position':'fixed','top':'0','left':'0','zIndex':'200',
    }, children=[
        html.Div(style={'padding':'20px 16px 16px','borderBottom':f'1px solid {db.BD}'}, children=[
            html.Div(style={'textAlign':'center'}, children=[
                html.Img(src='/assets/Logo_NUOL-ORiginal.png', style={
                    'width':'130px','height':'130px',
                    'objectFit':'contain',
                    'display':'block',
                    'margin':'0 auto 6px auto'
                }),
                html.Div([
                    html.Div('ລະບົບວິເຄາະແນວໂນ້ມ', style={
                        'fontSize':'17px','fontWeight':'600','color':db.TX2,
                        'fontFamily':'Noto Sans Lao,Segoe UI,Arial,sans-serif'
                    }),
                    html.Div('ຜົນການຮຽນຂອງນັກສຶກສາ', style={
                        'fontSize':'13px','color':db.TX,
                        'fontFamily':'Noto Sans Lao,Segoe UI,Arial,sans-serif'
                    }),
                ])
            ])
        ]),
        html.Div(style={'padding':'12px 0','flex':'1'}, children=[
            html.Div('ເມນູຫຼັກ', style={
                'fontSize':'10px','fontWeight':'600','color':"#000000",
                'padding':'4px 24px 8px','letterSpacing':'.06em',
                'textTransform':'uppercase',
                'fontFamily':'Noto Sans Lao,Segoe UI,Arial,sans-serif'
            }),
            *items
        ]),
        html.Div(style={'padding':'14px 16px','borderTop':f'1px solid {db.BD}'}, children=[
            html.Div(f'{db.total} ນ.ສ · {db.total_subj} ວິຊາ', style={
                'fontSize':'10px','color':'#B0BEC5',
                'fontFamily':'Noto Sans Lao,Segoe UI,Arial,sans-serif'
            }),
            html.Div('school_db · MySQL', style={
                'fontSize':'10px','color':'#CFD8DC','marginTop':'2px',
                'fontFamily':'Noto Sans Lao,Segoe UI,Arial,sans-serif'
            }),
        ])
    ])


from pages import dashboard, search, admin, predict

search.register_callbacks(app)
admin.register_callbacks(app)
dashboard.register_callbacks(app)
predict.register_callbacks(app)

app.layout = html.Div(style={
    'display':'flex','background':db.PAGE,'minHeight':'100vh',
    'fontFamily':'Noto Sans Lao,Segoe UI,Arial,sans-serif'
}, children=[
    html.Div(id='sidebar-slot'),
    html.Div(style={'marginLeft':'200px','flex':'1','minWidth':'0'}, children=[
        dcc.Location(id='url', refresh=False),
        html.Div(id='page-content')
    ]),
    html.Link(rel='stylesheet',
              href='https://fonts.googleapis.com/css2?family=Noto+Sans+Lao:wght@300;400;500;600;700&display=swap'),
])


@app.callback(
    Output('page-content','children'),
    Output('sidebar-slot','children'),
    Input('url','pathname')
)
def route(path):
    pages = {'/':dashboard.layout,'/search':search.layout,'/admin':admin.layout,'/predict':predict.layout}
    return pages.get(path, dashboard.layout), sidebar(path or '/')


from flask import send_file
import io, pandas as pd

@app.server.route('/export/students')
def export_students():
    import io, pandas as pd
    from flask import send_file
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as w:
        db.df_student.to_excel(w, index=False, sheet_name='ນັກສຶກສາ')
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name='students.xlsx',
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.server.route('/export/subjects')
def export_subjects():
    import io, pandas as pd
    from flask import send_file
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as w:
        db.df_subject.to_excel(w, index=False, sheet_name='ວິຊາ')
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name='subjects.xlsx',
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.server.route('/export/scores')
def export_scores():
    import io, pandas as pd
    from flask import send_file
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as w:
        db.df_score.to_excel(w, index=False, sheet_name='ຄະແນນ')
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name='scores.xlsx',
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.server.route('/export/<student_code>')
def export_excel(student_code):
    sc = db.df[db.df['student_code'] == student_code][
        ['semester','sem_order','subject_code','subject_name','grade','grade_point']
    ].sort_values('sem_order').drop(columns=['sem_order'])
    sc.columns = ['ພາກຮຽນ','ລະຫັດວິຊາ','ຊື່ວິຊາ','ເກຣດ','ຄະແນນ']

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        sc.to_excel(writer, index=False, sheet_name='ຄະແນນ')
    buf.seek(0)
    return send_file(buf, as_attachment=True,
                     download_name=f'{student_code}_grades.xlsx',
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


if __name__ == '__main__':
    print("✓ Dashboard at http://127.0.0.1:8050")
    app.run(debug=False)