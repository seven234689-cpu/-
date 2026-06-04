# app.py — CS Dashboard · Main App with Auth Routing
from dash import Dash, dcc, html, Input, Output, State, no_update
from flask import session as flask_session, redirect
import db

app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server
server.secret_key = "cs_nuol_secret_2025"
app.title = "ລະບົບວິເຄາະຜົນການຮຽນ CS"

# ── Sidebar (white, for dashboard pages) ──────────────────────────────────────
NAV = [
    {'href': '/dashboard', 'label': 'Dashboard'},
    {'href': '/search',  'label': 'ຄົ້ນຫານັກສຶກສາ'},
    {'href': '/predict', 'label': 'ທຳນາຍ GPA'},
    {'href': '/admin',   'label': 'Admin'},
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
                    'color': db.BLUE if is_a else db.TX,
                    'fontFamily':'Noto Sans Lao,Segoe UI,Arial,sans-serif',
                })
            ]),
            href=nav['href'], style={'textDecoration':'none'}
        ))

    return html.Div(style={
        'width':'200px','minHeight':'100vh','background':'white',
        'borderRight':f'1px solid {db.BD}','display':'flex',
        'flexDirection':'column','position':'fixed','top':'0','left':'0','zIndex':'200',
    }, children=[
        # Logo
        html.Div(style={'padding':'20px 16px 16px','borderBottom':f'1px solid {db.BD}'}, children=[
            html.Div(style={'textAlign':'center'}, children=[
                html.Img(src='/assets/Logo_NUOL-ORiginal.png', style={
                    'width':'130px','height':'130px','objectFit':'contain',
                    'display':'block','margin':'0 auto 6px auto',
                }),
                html.Div('ລະບົບວິເຄາະແນວໂນ້ມ', style={
                    'fontSize':'17px','fontWeight':'600','color':db.TX2,
                    'fontFamily':'Noto Sans Lao,Segoe UI,Arial,sans-serif',
                }),
                html.Div('ຜົນການຮຽນຂອງນັກສຶກສາ', style={
                    'fontSize':'13px','color':db.TX,
                    'fontFamily':'Noto Sans Lao,Segoe UI,Arial,sans-serif',
                }),
            ])
        ]),
        # Menu
        html.Div(style={'padding':'12px 0','flex':'1'}, children=[
            html.Div('ເມນູຫຼັກ', style={
                'fontSize':'10px','fontWeight':'600','color':'#000',
                'padding':'4px 24px 8px','letterSpacing':'.06em',
                'textTransform':'uppercase',
                'fontFamily':'Noto Sans Lao,Segoe UI,Arial,sans-serif',
            }),
            *items,
        ]),
        # Footer + Logout
        html.Div(style={'padding':'14px 16px','borderTop':f'1px solid {db.BD}'}, children=[
            html.Div(f'{db.total} ນ.ສ · {db.total_subj} ວິຊາ', style={
                'fontSize':'10px','color':'#B0BEC5',
                'fontFamily':'Noto Sans Lao,Segoe UI,Arial,sans-serif',
            }),
            html.Div('school_db · MySQL', style={
                'fontSize':'10px','color':'#CFD8DC','marginTop':'2px',
                'fontFamily':'Noto Sans Lao,Segoe UI,Arial,sans-serif',
            }),
            dcc.Link(
                html.Button('ອອກຈາກລະບົບ', style={
                    'width':'100%','marginTop':'10px','padding':'9px',
                    'background':'#FFEBEE','color':'#C62828',
                    'border':'1px solid #FFCDD2','borderRadius':'8px',
                    'fontSize':'12px','fontWeight':'600','cursor':'pointer',
                    'fontFamily':'Noto Sans Lao,Segoe UI,Arial,sans-serif',
                }),
                href='/do-logout', style={'textDecoration':'none'}
            ),
        ]),
    ])

# ── Register page callbacks ───────────────────────────────────────────────────
from pages import dashboard, search, admin, predict
from pages import login as login_page

login_page.register_callbacks(app)
search.register_callbacks(app)
admin.register_callbacks(app)
dashboard.register_callbacks(app)
predict.register_callbacks(app)

# ── Root layout ───────────────────────────────────────────────────────────────
app.layout = html.Div(style={
    'fontFamily':'Noto Sans Lao,Segoe UI,Arial,sans-serif',
}, children=[
    # No dcc.Store — ใช้ Flask session แทน
    html.Div(id='sidebar-slot'),
    dcc.Location(id='url', refresh=True),
    html.Div(id='page-content'),
    html.Link(rel='stylesheet',
              href='https://fonts.googleapis.com/css2?family=Noto+Sans+Lao:wght@300;400;500;600;700&display=swap'),
])

# ── Router ────────────────────────────────────────────────────────────────────
@app.callback(
    Output('page-content', 'children'),
    Output('sidebar-slot', 'children'),
    Input('url', 'pathname'),
)
def router(path):
    path = path or '/login'

    # Login page
    if path in ('/login', '/', '/logout'):
        return login_page.layout, html.Div()

    # Protected pages — เช็ค Flask session
    dashboard_pages = {
        '/dashboard': dashboard.layout,
        '/search':    search.layout,
        '/predict':   predict.layout,
        '/admin':     admin.layout,
    }
    if path in dashboard_pages:
        # ไม่มี session → กลับ login
        if not flask_session.get('email'):
            return login_page.layout, html.Div()
        # มี session → แสดงหน้า
        page = html.Div(style={'marginLeft':'200px','flex':'1','minWidth':'0',
                                'background':'#F5F6FA','minHeight':'100vh'}, children=[
            dashboard_pages[path]
        ])
        return page, sidebar(path)

    return login_page.layout, html.Div()

# ── Flask Routes ──────────────────────────────────────────────────────────────
from flask import send_file

@app.server.route('/do-logout')
def do_logout():
    flask_session.clear()
    return redirect('/login')

import io, pandas as pd

@app.server.route('/export/students')
def export_students():
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as w:
        db.df_student.to_excel(w, index=False, sheet_name='ນັກສຶກສາ')
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name='students.xlsx',
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.server.route('/export/subjects')
def export_subjects():
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as w:
        db.df_subject.to_excel(w, index=False, sheet_name='ວິຊາ')
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name='subjects.xlsx',
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.server.route('/export/scores')
def export_scores():
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
    with pd.ExcelWriter(buf, engine='openpyxl') as w:
        sc.to_excel(w, index=False, sheet_name='ຄະແນນ')
    buf.seek(0)
    return send_file(buf, as_attachment=True,
                     download_name=f'{student_code}_grades.xlsx',
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("✓ http://127.0.0.1:8050")
    app.run(debug=False)