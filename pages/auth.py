import dash
from dash import html, dcc, Input, Output, State, callback, ctx
from werkzeug.security import check_password_hash, generate_password_hash
from database import SessionLocal
from models import User
from datetime import datetime

dash.register_page(__name__, path="/auth", name="Connexion")

ROLES = [
    ("admin",     "◈", "Directeur"),
    ("teacher",   "◉", "Enseignant"),
    ("student",   "◆", "Etudiant"),
    ("parent",    "◎", "Parent"),
    ("secretary", "▣", "Secretaire"),
]

def layout():
    return html.Div([
        html.Div([
            # Logo
            html.Div("Nafa Scolaire", className="login-title"),
            html.Div("Système de Gestion Académique", className="login-subtitle"),

            # Onglets
            html.Div([
                html.Button("CONNEXION",   id="tab-login",    n_clicks=0,
                            className="login-tab login-tab-active"),
                html.Button("INSCRIPTION", id="tab-register", n_clicks=0,
                            className="login-tab"),
            ], style={"display":"flex","borderBottom":"1px solid var(--border)",
                      "marginBottom":"28px","gap":"0"}),

            # ── PANNEAU CONNEXION ──
            html.Div([
                # Boutons rôle
                html.Div("Je suis...", className="sga-label",
                         style={"marginBottom":"10px"}),
                html.Div([
                    html.Button([
                        html.Span(icon, style={"fontSize":"16px","display":"block","marginBottom":"3px"}),
                        html.Span(label, style={"fontSize":"9px","letterSpacing":"1px"}),
                    ], id=f"role-btn-{role}", n_clicks=0,
                    style={"flex":"1","padding":"10px 4px","cursor":"pointer",
                           "background":"var(--bg-primary)","border":"1px solid var(--border)",
                           "borderRadius":"4px","color":"var(--muted)",
                           "fontFamily":"Plus Jakarta Sans,sans-serif","textAlign":"center",
                           "display":"flex","flexDirection":"column","alignItems":"center",
                           "transition":"all 0.2s","fontSize":"12px"})
                    for role, icon, label in ROLES
                ], style={"display":"flex","gap":"6px","marginBottom":"20px"}),

                html.Div("Identifiant", className="sga-label"),
                dcc.Input(id="login-user", type="text",
                          placeholder="ex: admin",
                          debounce=False,
                          className="sga-input",
                          style={"width":"100%","marginBottom":"14px"}),

                html.Div("Mot de passe", className="sga-label"),
                dcc.Input(id="login-pass", type="password",
                          placeholder="........",
                          debounce=False,
                          className="sga-input",
                          style={"width":"100%","marginBottom":"20px"}),

                html.Button("SE CONNECTER →", id="btn-login-submit",
                            n_clicks=0,
                            className="btn-sga btn-gold",
                            style={"width":"100%","justifyContent":"center",
                                   "fontSize":"12px","padding":"14px"}),

                html.Div(id="login-feedback", style={"marginTop":"12px"}),

                # Comptes démo
                html.Div([
                    html.Div("Comptes démo :", style={"fontSize":"10px","color":"var(--muted)",
                             "marginBottom":"8px","letterSpacing":"1px","fontWeight":"600",
                             "textTransform":"uppercase"}),
                    *[html.Div([
                        html.Span(idf, style={"fontFamily":"monospace",
                                              "fontWeight":"700","color":"var(--em)",
                                              "fontSize":"12px","minWidth":"130px",
                                              "display":"inline-block"}),
                        html.Span(" / " + pwd, style={"fontFamily":"monospace",
                                                       "fontSize":"12px","color":"var(--text-primary)",
                                                       "marginRight":"8px"}),
                        html.Span(lbl, style={"fontSize":"10px","color":"var(--muted)"}),
                    ], style={"marginBottom":"4px"})
                    for idf, pwd, lbl in [
                        ("admin",       "admin123",  "Directeur"),
                        ("prof.diallo", "prof2026",  "Enseignant"),
                        ("secretaire",  "sec123",    "Secrétaire"),
                        ("demo.parent", "parent123", "Parent"),
                        ("demo.etudiant","etu2026",  "Étudiant"),
                    ]],
                    html.Div("→ Enseignants : prof.fall, prof.ba, prof.sow… / prof2026",
                             style={"fontSize":"10px","color":"var(--muted)","marginTop":"6px","fontStyle":"italic"}),
                    html.Div("→ Étudiants : prenom.nom / etu2026",
                             style={"fontSize":"10px","color":"var(--muted)","fontStyle":"italic"}),
                ], style={"marginTop":"16px","padding":"14px",
                          "background":"var(--em-xpale)",
                          "borderRadius":"8px","border":"1px solid rgba(14,102,85,0.15)"}),

            ], id="panel-login", style={"display":"block"}),

            # ── PANNEAU INSCRIPTION ──
            html.Div([
                html.Div("Identifiant", className="sga-label"),
                dcc.Input(id="reg-user", type="text",
                          placeholder="prenom.nom",
                          debounce=False,
                          className="sga-input",
                          style={"width":"100%","marginBottom":"14px"}),

                html.Div("Mot de passe", className="sga-label"),
                dcc.Input(id="reg-pass", type="password",
                          placeholder="Choisir un mot de passe",
                          debounce=False,
                          className="sga-input",
                          style={"width":"100%","marginBottom":"14px"}),

                html.Div("Role", className="sga-label"),
                dcc.Dropdown(id="reg-role",
                             options=[
                                 {"label":"Directeur / Admin",  "value":"admin"},
                                 {"label":"Enseignant",         "value":"teacher"},
                                 {"label":"Etudiant",           "value":"student"},
                                 {"label":"Parent",             "value":"parent"},
                                 {"label":"Secretaire",         "value":"secretary"},
                             ],
                             placeholder="Selectionner un role...",
                             clearable=False,
                             style={"marginBottom":"20px"}),

                html.Button("CREER MON COMPTE →", id="btn-register-submit",
                            n_clicks=0,
                            className="btn-sga btn-gold",
                            style={"width":"100%","justifyContent":"center",
                                   "fontSize":"12px","padding":"14px"}),

                html.Div(id="register-feedback", style={"marginTop":"12px"}),

            ], id="panel-register", style={"display":"none"}),

            # Stores et redirect
            dcc.Location(id="auth-redir"),
            dcc.Store(id="auth-role-store", data="admin"),

            html.Div(dcc.Link("← Retour a l'accueil", href="/accueil",
                     style={"fontSize":"11px","color":"var(--muted)","textDecoration":"none"}),
                     style={"textAlign":"center","marginTop":"20px"}),

        ], className="login-box"),
    ], className="login-page")


# ── Switcher onglets ──────────────────────────────────────────────────────────
@callback(
    Output("panel-login",    "style"),
    Output("panel-register", "style"),
    Output("tab-login",      "className"),
    Output("tab-register",   "className"),
    Input("tab-login",    "n_clicks"),
    Input("tab-register", "n_clicks"),
    prevent_initial_call=True,
)
def switch_tab(n_login, n_reg):
    show   = {"display":"block"}
    hide   = {"display":"none"}
    active = "login-tab login-tab-active"
    normal = "login-tab"
    if ctx.triggered_id == "tab-register":
        return hide, show, normal, active
    return show, hide, active, normal


# ── Highlight rôle sélectionné ────────────────────────────────────────────────
@callback(
    *[Output(f"role-btn-{r}", "style") for r, _, __ in ROLES],
    Output("auth-role-store", "data"),
    *[Input(f"role-btn-{r}", "n_clicks") for r, _, __ in ROLES],
    State("auth-role-store", "data"),
    prevent_initial_call=True,
)
def select_role(*args):
    roles   = [r for r, _, __ in ROLES]
    current = args[5]
    selected = current
    if ctx.triggered_id:
        selected = ctx.triggered_id.replace("role-btn-", "")

    styles = []
    for r in roles:
        if r == selected:
            styles.append({"flex":"1","padding":"10px 4px","cursor":"pointer",
                           "background":"rgba(14,102,85,0.12)",
                           "border":"2px solid var(--em)","borderRadius":"4px",
                           "color":"var(--em)","fontFamily":"Plus Jakarta Sans,sans-serif",
                           "textAlign":"center","display":"flex","flexDirection":"column",
                           "alignItems":"center","fontWeight":"700","transition":"all 0.2s",
                           "fontSize":"12px"})
        else:
            styles.append({"flex":"1","padding":"10px 4px","cursor":"pointer",
                           "background":"var(--bg-primary)","border":"1px solid var(--border)",
                           "borderRadius":"4px","color":"var(--muted)",
                           "fontFamily":"Plus Jakarta Sans,sans-serif","textAlign":"center",
                           "display":"flex","flexDirection":"column","alignItems":"center",
                           "transition":"all 0.2s","fontSize":"12px"})
    return *styles, selected


# ── Connexion ─────────────────────────────────────────────────────────────────
@callback(
    Output("login-feedback", "children"),
    Output("auth-redir",     "pathname"),
    Output("session-store",  "data"),
    Input("btn-login-submit","n_clicks"),
    State("login-user",      "value"),
    State("login-pass",      "value"),
    prevent_initial_call=True,
)
def do_login(n, username, pwd):
    if not n or n == 0:
        return dash.no_update, dash.no_update, dash.no_update

    username = (username or "").strip()
    pwd      = (pwd or "").strip()

    if not username or not pwd:
        return (html.Div("Remplissez les deux champs.",
                         className="sga-alert sga-alert-warning"),
                dash.no_update, dash.no_update)

    db = SessionLocal()
    u  = db.query(User).filter(User.username == username).first()
    db.close()

    if u is None:
        return (html.Div(f"Compte introuvable : {username}",
                         className="sga-alert sga-alert-danger"),
                dash.no_update, dash.no_update)

    if not check_password_hash(u.password_hash, pwd):
        return (html.Div("Mot de passe incorrect.",
                         className="sga-alert sga-alert-danger"),
                dash.no_update, dash.no_update)

    role = u.role or "teacher"
    session_data = {
        "logged_in": True,
        "username":  u.username,
        "role":      role,
        "linked_id": getattr(u, "linked_id", None),
        "user_id":   u.id,
    }
    redirects = {
        "admin":     "/",
        "teacher":   "/",
        "secretary": "/portail-secretaire",
        "student":   "/portail-etudiant",
        "parent":    "/portail-parent",
    }
    return dash.no_update, redirects.get(role, "/"), session_data


# ── Inscription ───────────────────────────────────────────────────────────────
@callback(
    Output("register-feedback", "children"),
    Input("btn-register-submit","n_clicks"),
    State("reg-user",  "value"),
    State("reg-pass",  "value"),
    State("reg-role",  "value"),
    prevent_initial_call=True,
)
def do_register(n, username, pwd, role):
    if not n or n == 0:
        return dash.no_update

    username = (username or "").strip()
    pwd      = (pwd or "").strip()

    if not username or not pwd or not role:
        return html.Div("Tous les champs sont requis.",
                        className="sga-alert sga-alert-warning")

    db = SessionLocal()
    try:
        if db.query(User).filter(User.username == username).first():
            return html.Div(f"L'identifiant {username!r} est deja utilise.",
                            className="sga-alert sga-alert-danger")
        u = User()
        u.username      = username
        u.password_hash = generate_password_hash(pwd)
        u.role          = role
        u.linked_id     = None
        u.created_at    = datetime.now()
        db.add(u)
        db.commit()
        return html.Div(f"Compte {username!r} cree. Connectez-vous maintenant.",
                        className="sga-alert sga-alert-success")
    except Exception as e:
        db.rollback()
        return html.Div(str(e), className="sga-alert sga-alert-danger")
    finally:
        db.close()
