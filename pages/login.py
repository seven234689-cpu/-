# pages/login.py — Dark Glassmorphism Login & Register
import re
from dash import html, dcc, Input, Output, State, callback_context, no_update
import auth
from flask import session as flask_session

FONT   = "Inter,'Noto Sans Lao',Segoe UI,Arial,sans-serif"
ACCENT = "#5b8dee"
PURPLE = "#8b5cf6"
GREEN  = "#10b981"
RED    = "#f43f5e"
YELLOW = "#fbbf24"
TX     = "#1E2A3A"
TX2    = "#546078"

TAB_ON = {
    "flex":"1","padding":"15px","background":"none","border":"none",
    "borderBottom":f"2.5px solid {ACCENT}","color":ACCENT,
    "fontSize":"13px","fontWeight":"700","cursor":"pointer","fontFamily":FONT,
}
TAB_OFF = {
    "flex":"1","padding":"15px","background":"none","border":"none",
    "borderBottom":"2.5px solid transparent","color":TX2,
    "fontSize":"13px","fontWeight":"500","cursor":"pointer","fontFamily":FONT,
}
SHOW = {"padding":"32px 36px","display":"block"}
HIDE = {"padding":"32px 36px","display":"none"}

def lbl(t):
    return html.Div(t, style={
        "fontSize":"11px","fontWeight":"600","color":TX2,
        "marginBottom":"7px","letterSpacing":".06em",
        "textTransform":"uppercase","fontFamily":FONT,
    })

def inp(id_, type_="text", ph=""):
    ac = "email" if "email" in id_ else "off"
    return dcc.Input(id=id_, type=type_, placeholder=ph,
                     autoComplete=ac, name=id_,
                     style={
                         "width":"100%","height":"48px",
                         "padding":"0 14px","fontSize":"14px",
                         "background":"#FFFFFF",
                         "border":"1.5px solid #E8EBF0",
                         "borderRadius":"12px","color":"#1E2A3A",
                         "outline":"none","boxSizing":"border-box",
                         "fontFamily":FONT,"display":"block","marginBottom":"18px",
                         "WebkitTextFillColor":"#1E2A3A",
                     })

def pw_inp(id_, ph="••••••••"):
    return html.Div(style={"position":"relative","marginBottom":"18px"}, children=[
        dcc.Input(id=id_, type="password", placeholder=ph,
                  autoComplete="new-password", name=id_,
                  style={
                      "width":"100%","height":"48px",
                      "padding":"0 48px 0 14px","fontSize":"14px",
                      "background":"#FFFFFF",
                      "border":"1.5px solid #E8EBF0",
                      "borderRadius":"12px","color":"#1E2A3A",
                      "outline":"none","boxSizing":"border-box",
                      "fontFamily":FONT,"display":"block",
                  }),
        html.Button("👁", id=f"{id_}-eye", n_clicks=0, style={
            "position":"absolute","right":"14px","top":"50%",
            "transform":"translateY(-50%)",
            "background":"none","border":"none","cursor":"pointer",
            "fontSize":"15px","color":TX2,"padding":"0",
        }),
    ])

def submit_btn(label, bid, color=ACCENT):
    return html.Button(label, id=bid, n_clicks=0, style={
        "width":"100%","height":"50px","marginTop":"6px",
        "background":f"linear-gradient(135deg,{color} 0%,{PURPLE} 100%)",
        "color":"white","border":"none","borderRadius":"12px",
        "fontSize":"15px","fontWeight":"700","cursor":"pointer",
        "fontFamily":FONT,"boxShadow":f"0 4px 20px {color}44",
    })

def alert_box(msg, kind="error"):
    cfg = {
        "error":   (RED,   "rgba(244,63,94,.12)",  "rgba(244,63,94,.3)",  "✗"),
        "success": (GREEN, "rgba(16,185,129,.12)", "rgba(16,185,129,.3)", "✓"),
    }
    fg, bg, bd, icon = cfg.get(kind, cfg["error"])
    return html.Div(style={
        "background":bg,"border":f"1px solid {bd}","borderRadius":"10px",
        "padding":"11px 14px","display":"flex","alignItems":"center",
        "gap":"9px","fontFamily":FONT,"marginTop":"12px",
    }, children=[
        html.Span(icon, style={"color":fg,"fontWeight":"700","fontSize":"14px","flexShrink":"0"}),
        html.Span(msg,  style={"color":fg,"fontSize":"13px","fontWeight":"500"}),
    ])

# ── Layout ────────────────────────────────────────────────────────────────────
layout = html.Div(style={
    "minHeight":"100vh",
    "background":"linear-gradient(135deg,#EEF2F9 0%,#F0F4FF 50%,#F5F6FA 100%)",
    "display":"flex","flexDirection":"column",
    "alignItems":"center","justifyContent":"center",
    "padding":"32px 16px","fontFamily":FONT,
}, children=[
    dcc.Location(id="login-url", refresh=True),

    # Glow blobs
    html.Div(style={
        "position":"fixed","width":"500px","height":"500px","borderRadius":"50%",
        "background":"radial-gradient(circle,rgba(91,141,238,.10) 0%,transparent 70%)",
        "top":"-160px","left":"-160px","pointerEvents":"none",
    }),
    html.Div(style={
        "position":"fixed","width":"420px","height":"420px","borderRadius":"50%",
        "background":"radial-gradient(circle,rgba(139,92,246,.07) 0%,transparent 70%)",
        "bottom":"-120px","right":"-120px","pointerEvents":"none",
    }),

    # Logo
    html.Div(style={"textAlign":"center","marginBottom":"28px","position":"relative","zIndex":"1"}, children=[
        html.Div(style={
            "width":"170px","height":"170px","borderRadius":"50%","margin":"0 auto 14px",
            "background":"rgba(91,141,238,.12)",
            "border":"1.5px solid rgba(91,141,238,.28)",
            "display":"flex","alignItems":"center","justifyContent":"center",
            "boxShadow":"0 0 40px rgba(91,141,238,.22)",
        }, children=[
            html.Img(src="/assets/Logo_NUOL-ORiginal.png",
                     style={"width":"150px","height":"150px","objectFit":"contain"}),
        ]),
        html.Div("ລະບົບວິເຄາະແນວໂນ້ມ ຜົນການຮຽນນັກສຶກສາ", style={
            "fontSize":"18px","fontWeight":"700","color":"#1E2A3A","fontFamily":FONT,
        }),
        html.Div("ພາກວິຊາ ຄອມພິວເຕີ · ມະຫາວິທະຍາໄລແຫ່ງຊາດ", style={
            "fontSize":"12px","color":TX2,"marginTop":"5px","fontFamily":FONT,
        }),
    ]),

    # Card
    html.Div(style={
        "width":"100%","maxWidth":"430px","position":"relative","zIndex":"1",
        "background":"rgba(255,255,255,0.88)",
        "backdropFilter":"blur(28px)","-webkit-backdropFilter":"blur(28px)",
        "border":"1px solid #E0E8F4",
        "borderRadius":"20px",
        "boxShadow":"0 8px 40px rgba(91,141,238,.10), 0 2px 8px rgba(0,0,0,.05)",
        "overflow":"hidden",
    }, children=[

        # Tabs
        html.Div(style={
            "display":"flex",
            "borderBottom":"1px solid #E8EBF0",
            "background":"#F8FAFD",
        }, children=[
            html.Button("ເຂົ້າສູ່ລະບົບ", id="tab-login",    n_clicks=1, style=TAB_ON),
            html.Button("ລົງທະບຽນ",     id="tab-register", n_clicks=0, style=TAB_OFF),
        ]),

        # ── Login panel ────────────────────────────────────────
        html.Div(id="form-login", style=SHOW, children=[
            html.Div("ຍິນດີຕ້ອນຮັບ ", style={
                "fontSize":"22px","fontWeight":"800","color":"#1E2A3A","fontFamily":FONT,"marginBottom":"4px",
            }),
            html.Div("ໃສ່ອີເມລ ແລະ ລະຫັດຜ່ານຂອງທ່ານ", style={
                "fontSize":"13px","color":TX2,"fontFamily":FONT,"marginBottom":"26px",
            }),
            lbl("ອີເມລ"),
            inp("login-email", "text", "example@email.com"),
            lbl("ລະຫັດຜ່ານ"),
            pw_inp("login-password"),
            html.Div(id="login-msg", style={"minHeight":"20px"}),
            submit_btn("ເຂົ້າສູ່ລະບົບ", "btn-login", ACCENT),
        ]),

        # ── Register panel ─────────────────────────────────────
        html.Div(id="form-register", style=HIDE, children=[
            html.Div("ສ້າງບັນຊີໃໝ່ ", style={
                "fontSize":"22px","fontWeight":"800","color":"#1E2A3A","fontFamily":FONT,"marginBottom":"4px",
            }),
            html.Div("ຕື່ມຂໍ້ມູນລຸ່ມນີ້ເພື່ອສ້າງບັນຊີ", style={
                "fontSize":"13px","color":TX2,"fontFamily":FONT,"marginBottom":"26px",
            }),
            lbl("ອີເມລ"),
            inp("reg-email", "text", "example@email.com"),
            lbl("ລະຫັດຜ່ານ (ຢ່າງໜ້ອຍ 6 ຕົວ)"),
            pw_inp("reg-password"),
            html.Div(id="pw-strength", style={"marginBottom":"14px","minHeight":"18px"}),
            lbl("ຢືນຢັນລະຫັດຜ່ານ"),
            pw_inp("reg-password2", "ພິມລະຫັດຜ່ານຄືນ"),
            html.Div(id="reg-msg", style={"minHeight":"20px"}),
            submit_btn("ລົງທະບຽນ", "btn-register", PURPLE),
        ]),
    ]),

    # Footer
    html.Div("© 2025 ມະຫາວິທະຍາໄລແຫ່ງຊາດ · ພັດທະນາໂດຍ CS Department", style={
        "marginTop":"24px","fontSize":"11px","color":"rgba(80,100,140,.35)",
        "fontFamily":FONT,"position":"relative","zIndex":"1",
    }),

])

# ── Callbacks ─────────────────────────────────────────────────────────────────
def register_callbacks(app):

    # Tab toggle
    @app.callback(
        Output("form-login",    "style"),
        Output("form-register", "style"),
        Output("tab-login",     "style"),
        Output("tab-register",  "style"),
        Input("tab-login",    "n_clicks"),
        Input("tab-register", "n_clicks"),
        prevent_initial_call=True,
    )
    def toggle_tab(n1, n2):
        trig = callback_context.triggered[0]["prop_id"].split(".")[0]
        if trig == "tab-register":
            return HIDE, SHOW, TAB_OFF, TAB_ON
        return SHOW, HIDE, TAB_ON, TAB_OFF

    # Show/hide passwords
    @app.callback(
        Output("login-password", "type"),
        Output("login-password-eye", "children"),
        Input("login-password-eye", "n_clicks"),
        prevent_initial_call=True,
    )
    def eye_login(n):
        return ("text","🙈") if n%2==1 else ("password","👁")

    @app.callback(
        Output("reg-password", "type"),
        Output("reg-password-eye", "children"),
        Input("reg-password-eye", "n_clicks"),
        prevent_initial_call=True,
    )
    def eye_reg(n):
        return ("text","🙈") if n%2==1 else ("password","👁")

    @app.callback(
        Output("reg-password2", "type"),
        Output("reg-password2-eye", "children"),
        Input("reg-password2-eye", "n_clicks"),
        prevent_initial_call=True,
    )
    def eye_reg2(n):
        return ("text","🙈") if n%2==1 else ("password","👁")

    # Password strength bar
    @app.callback(
        Output("pw-strength", "children"),
        Input("reg-password", "value"),
        prevent_initial_call=True,
    )
    def pw_strength(pw):
        if not pw:
            return ""
        s = sum([len(pw)>=6, len(pw)>=10,
                 bool(re.search(r'[A-Z]',pw)),
                 bool(re.search(r'\d',pw)),
                 bool(re.search(r'[!@#$%^&*]',pw))])
        if s<=2:   c,t,w = RED,    "ອ່ອນ",   "28%"
        elif s==3: c,t,w = YELLOW, "ປານກາງ", "58%"
        else:      c,t,w = GREEN,  "ແຂງແຮງ", "100%"
        return html.Div(style={"display":"flex","alignItems":"center","gap":"10px"}, children=[
            html.Div(style={"flex":"1","height":"4px","background":"rgba(255,255,255,.08)","borderRadius":"2px"}, children=[
                html.Div(style={"width":w,"height":"100%","background":c,"borderRadius":"2px","transition":"width .3s"})
            ]),
            html.Span(t, style={"fontSize":"11px","color":c,"fontFamily":FONT,"fontWeight":"600","minWidth":"52px"}),
        ])

    # Login
    @app.callback(
        Output("login-msg", "children"),
        Output("login-url", "href"),
        Input("btn-login",  "n_clicks"),
        State("login-email",    "value"),
        State("login-password", "value"),
        prevent_initial_call=True,
    )
    def do_login(n, email, pw):
        def err(m): return alert_box(m), no_update
        if not email or not email.strip():
            return err("ກະລຸນາໃສ່ອີເມລ")
        if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email.strip()):
            return err("ຮູບແບບອີເມລບໍ່ຖືກຕ້ອງ")
        if not pw:
            return err("ກະລຸນາໃສ່ລະຫັດຜ່ານ")
        ok, msg = auth.login_user(email.strip(), pw)
        if ok:
            flask_session['email'] = email.lower().strip()
            return alert_box("ເຂົ້າສູ່ລະບົບສໍາເລັດ ✓", "success"), "/dashboard"
        return err(msg)

    # Register
    @app.callback(
        Output("reg-msg",       "children"),
        Output("form-login",    "style", allow_duplicate=True),
        Output("form-register", "style", allow_duplicate=True),
        Output("tab-login",     "style", allow_duplicate=True),
        Output("tab-register",  "style", allow_duplicate=True),
        Input("btn-register", "n_clicks"),
        State("reg-email",     "value"),
        State("reg-password",  "value"),
        State("reg-password2", "value"),
        prevent_initial_call=True,
    )
    def do_register(n, email, pw, pw2):
        def err(m): return alert_box(m), no_update, no_update, no_update, no_update
        if not email or not email.strip():
            return err("ກະລຸນາໃສ່ອີເມລ")
        if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email.strip()):
            return err("ຮູບແບບອີເມລບໍ່ຖືກຕ້ອງ")
        if not pw:
            return err("ກະລຸນາໃສ່ລະຫັດຜ່ານ")
        if len(pw) < 6:
            return err("ລະຫັດຜ່ານຕ້ອງມີຢ່າງໜ້ອຍ 6 ຕົວ")
        if not pw2:
            return err("ກະລຸນາຢືນຢັນລະຫັດຜ່ານ")
        if pw != pw2:
            return err("ລະຫັດຜ່ານທັງສອງບໍ່ຕົງກັນ ❌")
        ok, msg = auth.register_user(email.strip(), pw)
        if ok:
            return (alert_box("ລົງທະບຽນສໍາເລັດ! ກະລຸນາເຂົ້າສູ່ລະບົບ ✓", "success"),
                    SHOW, HIDE, TAB_ON, TAB_OFF)
        return err(msg)