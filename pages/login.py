# pages/login.py — Flat Light Login & Register (separate pages)
import re
from dash import html, dcc, Input, Output, State, no_update
import auth
from flask import session as flask_session

FONT   = "Inter,'Noto Sans Lao',Segoe UI,Arial,sans-serif"
ACCENT = "#2D6CDF"
PURPLE = "#6C63FF"
GREEN  = "#1B8A5A"
RED    = "#E0383D"
YELLOW = "#E8A33D"
TX     = "#1E2A3A"
TX2    = "#7A8699"
BG     = "#F4F6F9"
FIELD_BG = "#F1F3F6"

def inp(id_, type_="text", ph=""):
    ac = "email" if "email" in id_ else "off"
    return dcc.Input(id=id_, type=type_, placeholder=ph,
                     autoComplete=ac, name=id_,
                     style={
                         "width":"100%","height":"46px",
                         "padding":"0 16px","fontSize":"14px",
                         "background":FIELD_BG,
                         "border":"none",
                         "borderRadius":"10px","color":TX,
                         "outline":"none","boxSizing":"border-box",
                         "fontFamily":FONT,"display":"block","marginBottom":"14px",
                         "WebkitTextFillColor":TX,
                     })

def pw_inp(id_, ph="ລະຫັດຜ່ານ"):
    return html.Div(style={"position":"relative","marginBottom":"14px"}, children=[
        dcc.Input(id=id_, type="password", placeholder=ph,
                  autoComplete="new-password", name=id_,
                  style={
                      "width":"100%","height":"46px",
                      "padding":"0 46px 0 16px","fontSize":"14px",
                      "background":FIELD_BG,
                      "border":"none",
                      "borderRadius":"10px","color":TX,
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
        "width":"100%","height":"46px","marginTop":"4px",
        "background":color,
        "color":"white","border":"none","borderRadius":"10px",
        "fontSize":"14px","fontWeight":"700","cursor":"pointer",
        "fontFamily":FONT,
    })

def alert_box(msg, kind="error"):
    cfg = {
        "error":   (RED,   "rgba(224,56,61,.08)",  "rgba(224,56,61,.25)",  "✗"),
        "success": (GREEN, "rgba(27,138,90,.08)",  "rgba(27,138,90,.25)",  "✓"),
    }
    fg, bg, bd, icon = cfg.get(kind, cfg["error"])
    return html.Div(style={
        "background":bg,"border":f"1px solid {bd}","borderRadius":"10px",
        "padding":"11px 14px","display":"flex","alignItems":"center",
        "gap":"9px","fontFamily":FONT,"marginTop":"10px",
    }, children=[
        html.Span(icon, style={"color":fg,"fontWeight":"700","fontSize":"14px","flexShrink":"0"}),
        html.Span(msg,  style={"color":fg,"fontSize":"13px","fontWeight":"500"}),
    ])

def page_shell(*, header_children, body_children, location_id):
    return html.Div(style={
        "minHeight":"100vh",
        "background":BG,
        "display":"flex","flexDirection":"column",
        "alignItems":"center","justifyContent":"center",
        "padding":"32px 16px","fontFamily":FONT,
    }, children=[
        dcc.Location(id=location_id, refresh=True),
        html.Div(style={
            "width":"100%","maxWidth":"430px",
            "background":"#FFFFFF",
            "border":"1px solid #E8EBF0",
            "borderRadius":"16px",
            "boxShadow":"0 4px 24px rgba(20,30,50,.06)",
            "overflow":"hidden",
        }, children=[
            html.Div(style={"textAlign":"center","padding":"36px 36px 8px"}, children=[
                html.Img(src="/assets/Logo_NUOL-ORiginal.png", style={
                    "width":"150px","height":"150px","objectFit":"contain","marginBottom":"12px",
                }),
                html.Div("ມະຫາວິທະຍາໄລແຫ່ງຊາດ", style={
                    "fontSize":"20px","fontWeight":"700","color":TX,"fontFamily":FONT,
                }),
                html.Div("ລະບົບວິເຄາະແນວໂນ້ມຜົນການຮຽນ", style={
                    "fontSize":"15px","color":TX2,"marginTop":"4px","fontFamily":FONT,
                }),
            ]),
            *header_children,
            html.Div(style={"padding":"8px 40px 36px"}, children=body_children),
        ]),
        html.Div("v1.0.0", style={
            "marginTop":"18px","fontSize":"11px","color":"#AEB7C4","fontFamily":FONT,
        }),
    ])

# ── Login page ───────────────────────────────────────────────────────────────
layout = page_shell(
    location_id="login-url",
    header_children=[
        html.Div("ເຂົ້າສູ່ລະບົບ", style={
            "textAlign":"center","fontSize":"15px","fontWeight":"700","color":ACCENT,
            "fontFamily":FONT,"margin":"4px 36px 0","padding":"12px 0",
            "borderBottom":f"2.5px solid {ACCENT}",
        }),
    ],
    body_children=[
        html.Div(style={"height":"10px"}),
        inp("login-email", "text", "ອີເມລ"),
        pw_inp("login-password", "ລະຫັດຜ່ານ"),
        dcc.Checklist(
            id="login-remember",
            options=[{"label": " ຈົດຈໍາການເຂົ້າສູ່ລະບົບ", "value": "remember"}],
            value=[],
            style={"fontSize":"12.5px","color":TX2,"fontFamily":FONT,"marginBottom":"18px"},
            inputStyle={"marginRight":"6px"},
        ),
        html.Div(id="login-msg", style={"minHeight":"6px"}),
        submit_btn("ເຂົ້າສູ່ລະບົບ", "btn-login", ACCENT),
        html.Div(style={"textAlign":"center","marginTop":"18px","fontSize":"12.5px","color":TX2,"fontFamily":FONT}, children=[
            "ບໍ່ມີບັນຊີເຂົ້າສູ່ລະບົບ? ",
            dcc.Link("ລົງທະບຽນ", href="/register", style={"color":ACCENT,"fontWeight":"600","textDecoration":"underline"}),
        ]),
    ],
)

# ── Register page ─────────────────────────────────────────────────────────────
register_layout = page_shell(
    location_id="register-url",
    header_children=[
        html.Div("ລົງທະບຽນ", style={
            "textAlign":"center","fontSize":"15px","fontWeight":"700","color":PURPLE,
            "fontFamily":FONT,"margin":"4px 36px 0","padding":"12px 0",
            "borderBottom":f"2.5px solid {PURPLE}",
        }),
    ],
    body_children=[
        html.Div(style={"height":"10px"}),
        inp("reg-email", "text", "ອີເມລ"),
        pw_inp("reg-password", "ລະຫັດຜ່ານ (ຢ່າງໜ້ອຍ 6 ຕົວ)"),
        html.Div(id="pw-strength", style={"marginBottom":"10px","minHeight":"18px"}),
        pw_inp("reg-password2", "ຢືນຢັນລະຫັດຜ່ານ"),
        html.Div(id="reg-msg", style={"minHeight":"6px"}),
        submit_btn("ລົງທະບຽນ", "btn-register", PURPLE),
        html.Div(style={"textAlign":"center","marginTop":"18px","fontSize":"12.5px","color":TX2,"fontFamily":FONT}, children=[
            "ມີບັນຊີແລ້ວ? ",
            dcc.Link("ເຂົ້າສູ່ລະບົບ", href="/login", style={"color":PURPLE,"fontWeight":"600","textDecoration":"underline"}),
        ]),
    ],
)

# ── Callbacks ─────────────────────────────────────────────────────────────────
def register_callbacks(app):

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
            html.Div(style={"flex":"1","height":"4px","background":"#E8EBF0","borderRadius":"2px"}, children=[
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
        ok, role_or_msg = auth.login_user(email.strip(), pw)
        if ok:
            flask_session['email'] = email.lower().strip()
            flask_session['role'] = role_or_msg
            return alert_box("ເຂົ້າສູ່ລະບົບສໍາເລັດ ✓", "success"), "/dashboard"
        return err(role_or_msg)

    # Register
    @app.callback(
        Output("reg-msg",     "children"),
        Output("register-url", "href"),
        Input("btn-register", "n_clicks"),
        State("reg-email",     "value"),
        State("reg-password",  "value"),
        State("reg-password2", "value"),
        prevent_initial_call=True,
    )
    def do_register(n, email, pw, pw2):
        def err(m): return alert_box(m), no_update
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
            return alert_box("ລົງທະບຽນສໍາເລັດ! ກະລຸນາເຂົ້າສູ່ລະບົບ ✓", "success"), no_update
        return err(msg)
