import pandas as pd
import numpy as np
import sqlalchemy
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from dash import html
import os
from dotenv import load_dotenv

load_dotenv()

HOST     = os.environ.get("DB_HOST", "localhost").strip()
PORT     = int(os.environ.get("DB_PORT", "3306").strip())
USER     = os.environ.get("DB_USER", "root").strip()
PASSWORD = os.environ.get("DB_PASSWORD", "").strip()
DATABASE = os.environ.get("DB_NAME", "school_db").strip()

engine = sqlalchemy.create_engine(
    f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}"
)
sem_order = ["1/I","1/II","2/I","2/II","3/I","3/II","4/I","4/II"]

MAJOR_MAP = {
    137: 'ວິທະຍາສາດຄອມພິວເຕີ',
    144: 'ການພັດທະນາເວັບໄຊ',
    149: 'ການພັດທະນາໂປຣແກຣມຄອມພິວເຕີ',
}

def credit_to_major(total_credit):
    return MAJOR_MAP.get(int(total_credit), 'ບໍ່ລະບຸ')

def reload_data():
    global df_student, df_subject, df_score, df, df_gpa
    global total, avgGPA, frate, high, mid, risk, male, female, total_subj
    global trend_all, trend_g, gd, subj_avg, hm_df, hp, km, sc_fit, CC, lm

    df_student = pd.read_sql("SELECT * FROM student", engine)
    df_subject = pd.read_sql("SELECT * FROM subject", engine)
    df_score   = pd.read_sql("SELECT * FROM score",   engine)

    # ── กรณี DB ว่างเปล่า ──
    if len(df_student) == 0 or len(df_score) == 0:
        df = pd.DataFrame(columns=['student_id','student_code','gender','major',
                                   'subject_id','subject_code','subject_name',
                                   'score_id','semester','grade','grade_point','sem_order'])
        df_gpa = pd.DataFrame(columns=['student_id','student_code','gender','gpa','cluster'])
        CC = {'ສູງ':'#2E7D32','ກາງ':'#1565C0','ສ່ຽງ':'#C62828'}
        sc_fit = StandardScaler()
        km = KMeans(n_clusters=3, random_state=42, n_init=10)
        lm = {}
        total=0; avgGPA=0.0; frate=0.0; high=0; mid=0; risk=0
        male=0; female=0; total_subj=0
        trend_all = pd.DataFrame(columns=['semester','sem_order','avg_gpa'])
        trend_g   = pd.DataFrame(columns=['semester','sem_order','gender','avg_gpa'])
        gd = pd.DataFrame({'grade':['A','B+','B','C+','C','D+','D','F'],'count':[0]*8})
        subj_avg  = pd.DataFrame(columns=['subject_code','subject_name','avg_gp','label'])
        hm_df     = pd.DataFrame(columns=['subject_code','semester','v'])
        hp        = pd.DataFrame()
        return

    grade_map = {'A':4.0,'B+':3.5,'B':3.0,'C+':2.5,'C':2.0,'D+':1.5,'D':1.0,'F':0.0}
    df_score['grade_point'] = df_score['grade'].map(grade_map)

    df = (df_score
          .merge(df_student, on='student_id', how='left')
          .merge(df_subject, on='subject_id', how='left'))
    # ແກ້ໄຂ: ເກັບ F ໄວ້ດ້ວຍ
    df = df[df['grade'].isin(grade_map.keys())]

    df['sem_order'] = df['semester'].apply(
        lambda x: sem_order.index(x) if x in sem_order else 99)
    df = df[df['sem_order'] != 99]

    df_gpa = (df.groupby(['student_id','student_code','gender'])['grade_point']
                .mean().reset_index(name='gpa'))
    df_gpa['gpa'] = df_gpa['gpa'].round(3)

    if 'major' in df_student.columns:
        df_gpa = df_gpa.merge(
            df_student[['student_id','major']], on='student_id', how='left')

    # ── กรณี df_gpa ว่าง ──
    if len(df_gpa) == 0:
        CC = {'ສູງ':'#2E7D32','ກາງ':'#1565C0','ສ່ຽງ':'#C62828'}
        sc_fit = StandardScaler()
        km = KMeans(n_clusters=3, random_state=42, n_init=10)
        lm = {}
        df_gpa['cluster'] = pd.Series(dtype=str)
        total=0; avgGPA=0.0; frate=0.0; high=0; mid=0; risk=0
        male=0; female=0; total_subj=0
        trend_all = pd.DataFrame(columns=['semester','sem_order','avg_gpa'])
        trend_g   = pd.DataFrame(columns=['semester','sem_order','gender','avg_gpa'])
        gd = pd.DataFrame({'grade':['A','B+','B','C+','C','D+','D','F'],'count':[0]*8})
        subj_avg  = pd.DataFrame(columns=['subject_code','subject_name','avg_gp','label'])
        hm_df     = pd.DataFrame(columns=['subject_code','semester','v'])
        hp        = pd.DataFrame()
        return

    if len(df_gpa) >= 3:
        sc_fit = StandardScaler()
        X = sc_fit.fit_transform(df_gpa[['gpa']].values)
        km = KMeans(n_clusters=3, random_state=42, n_init=10)
        df_gpa['cn'] = km.fit_predict(X)
        ci = np.argsort(sc_fit.inverse_transform(km.cluster_centers_).flatten())
        lm = {ci[0]:'ສ່ຽງ', ci[1]:'ກາງ', ci[2]:'ສູງ'}
        df_gpa['cluster'] = df_gpa['cn'].map(lm)
    else:
        sc_fit = StandardScaler()
        km = KMeans(n_clusters=3, random_state=42, n_init=10)
        lm = {}
        df_gpa['cluster'] = 'ກາງ'

    CC = {'ສູງ':'#2E7D32','ກາງ':'#1565C0','ສ່ຽງ':'#C62828'}

    total      = len(df_gpa)
    avgGPA     = round(df_gpa['gpa'].mean(), 2) if len(df_gpa) > 0 else 0.0
    frate      = round(df[df['grade']=='F'].shape[0]/len(df)*100, 1) if len(df) > 0 else 0
    high       = int((df_gpa['cluster']=='ສູງ').sum())
    mid        = int((df_gpa['cluster']=='ກາງ').sum())
    risk       = int((df_gpa['cluster']=='ສ່ຽງ').sum())
    male       = int((df_student['gender']=='M').sum())
    female     = int((df_student['gender']=='F').sum())
    total_subj = df['subject_code'].nunique() if len(df) > 0 else 0

    trend_all = (df.groupby(['semester','sem_order'])['grade_point']
                   .mean().reset_index(name='avg_gpa').sort_values('sem_order'))
    trend_all['avg_gpa'] = trend_all['avg_gpa'].round(3)

    trend_g = (df.groupby(['semester','sem_order','gender'])['grade_point']
                 .mean().reset_index(name='avg_gpa').sort_values('sem_order'))

    gd = df['grade'].value_counts().reindex(
        ['A','B+','B','C+','C','D+','D','F']).fillna(0).reset_index()
    gd.columns = ['grade','count']

    subj_avg = (df.groupby(['subject_code','subject_name'])['grade_point']
                  .mean().reset_index(name='avg_gp').sort_values('avg_gp'))
    subj_avg['avg_gp'] = subj_avg['avg_gp'].round(3)
    subj_avg['label'] = subj_avg['subject_code'] + '   ' + subj_avg['subject_name'].str[:28]

    hm_df = df.groupby(['subject_code','semester'])['grade_point'].mean().reset_index(name='v')
    hp = hm_df.pivot(index='subject_code', columns='semester', values='v')
    hp = hp.reindex(columns=[s for s in sem_order if s in hp.columns])

reload_data()

# ── Design Tokens ──────────────────────────────────────────
PAGE  = '#F5F6FA'
BG    = '#F5F6FA'
CARD  = '#FFFFFF'
BD    = '#E8EBF0'
TX    = '#546078'
TX2   = '#1E2A3A'
BLUE  = '#1565C0'
GREEN = '#2E7D32'
RED   = '#C62828'
FONT  = dict(family='Noto Sans Lao,Segoe UI,Arial,sans-serif', size=12, color=TX)

def chart_base(h=300, leg=False):
    return dict(
        plot_bgcolor='#FAFBFD', paper_bgcolor=CARD, font=FONT,
        height=h, margin=dict(t=24,b=48,l=56,r=24),
        showlegend=leg,
        legend=dict(orientation='h', y=1.08, x=0,
                    bgcolor='rgba(0,0,0,0)',
                    font=dict(size=12, color=TX2)),
        hoverlabel=dict(bgcolor='white', font_size=13,
                        font_color='#1E2A3A', bordercolor='#1E2A3A',
                        font_family='Noto Sans Lao,Segoe UI,Arial,sans-serif')
    )

def xax():
    return dict(showgrid=False, zeroline=False,
                color=TX, linecolor=BD, linewidth=1)

def yax():
    return dict(showgrid=True, gridcolor='#EEF0F5',
                zeroline=False, color=TX, linecolor=BD)

def card_style(accent=BLUE):
    return {
        'background': CARD,
        'border': f'1px solid {BD}',
        'borderRadius': '12px',
        'padding': '24px 26px',
        'marginBottom': '20px',
        'boxShadow': '0 2px 8px rgba(0,0,0,.04)',
        'borderLeft': f'4px solid {accent}'
    }

def sec_title(t):
    return html.Div(t, style={
        'fontSize':'14px', 'fontWeight':'600', 'color':TX2,
        'marginBottom':'4px',
        'fontFamily':'Noto Sans Lao,Segoe UI,Arial,sans-serif'
    })

def sec_sub(t):
    return html.Div(t, style={
        'fontSize':'12px', 'color':'#8A9BB0',
        'marginBottom':'16px',
        'fontFamily':'Noto Sans Lao,Segoe UI,Arial,sans-serif'
    })

def kpi_card(value, label, color, icon=''):
    return html.Div(style={
        'background': CARD,
        'border': f'1px solid {BD}',
        'borderRadius': '12px',
        'padding': '18px 16px',
        'textAlign': 'center',
        'flex': '1',
        'minWidth': '110px',
        'boxShadow': '0 1px 4px rgba(0,0,0,.04)',
        'borderTop': f'3px solid {color}'
    }, children=[
        html.Img(src=icon, style={
            'width': '32px', 'height': '32px',
            'objectFit': 'contain',
            'display': 'block',
            'margin': '0 auto 6px auto',
            'filter': 'grayscale(100%) brightness(0.2)',
        }) if icon else None,
        html.Div(str(value), style={
            'fontSize':'26px', 'fontWeight':'700',
            'color': color, 'lineHeight':'1.2'
        }),
        html.Div(label, style={
            'fontSize':'11px', 'color':TX,
            'marginTop':'5px', 'fontWeight':'500',
            'fontFamily':'Noto Sans Lao,Segoe UI,Arial,sans-serif'
        })
    ])