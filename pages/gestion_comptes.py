import dash
from dash import html, dcc, Input, Output, State, callback
from werkzeug.security import generate_password_hash
from database import SessionLocal
from models import User, Student
from datetime import datetime

dash.register_page(__name__, path="/gestion-comptes", name="Gestion des comptes")

ROLES = [
    {"label":"Directeur / Admin",  "value":"admin"},
    {"label":"Enseignant",         "value":"teacher"},
    {"label":"Étudiant",           "value":"student"},
    {"label":"Parent",             "value":"parent"},
    {"label":"Secrétaire",         "value":"secretary"},
]
ROLE_COLORS = {"admin":"var(--gold)","teacher":"var(--green)",
               "student":"#5A9BC2","parent":"var(--copper)","secretary":"var(--muted)"}
ROLE_ICONS  = {"admin":"◈","teacher":"◉","student":"◆","parent":"◎","secretary":"▣"}

def layout():
    db = SessionLocal()
    students = [(s.id, f"{s.nom} {s.prenom}") for s in db.query(Student).filter_by(actif=True).all()]
    db.close()
    stu_opts = [{"label":n,"value":sid} for sid,n in students]

    return html.Div([
        html.Div([
            html.Div([
                html.Div("Gestion des comptes", className="page-title"),
                html.Div("Créer et gérer les accès utilisateurs", className="page-subtitle"),
            ]),
        ], className="topbar"),

        html.Div([
            # Panneau création
            html.Div([
                html.Div([
                    html.Div("Créer un compte", className="sga-card-title",
                             style={"marginBottom":"20px"}),
                    html.Div([
                        html.Span("Rôle", className="sga-label"),
                        dcc.Dropdown(id="gc-role", options=ROLES,
                                     placeholder="Sélectionner un rôle…", clearable=False),
                    ], style={"marginBottom":"14px"}),
                    html.Div([
                        html.Span("Identifiant", className="sga-label"),
                        dcc.Input(id="gc-user", placeholder="prenom.nom",
                                  className="sga-input", style={"width":"100%"}),
                    ], style={"marginBottom":"14px"}),
                    html.Div([
                        html.Span("Mot de passe", className="sga-label"),
                        dcc.Input(id="gc-pass", type="password",
                                  placeholder="••••••••", className="sga-input",
                                  style={"width":"100%"}),
                    ], style={"marginBottom":"14px"}),
                    # Lien étudiant (pour student / parent)
                    html.Div([
                        html.Span("Lier à un étudiant", className="sga-label"),
                        dcc.Dropdown(id="gc-linked", options=stu_opts,
                                     placeholder="Pour rôle étudiant ou parent…"),
                    ], style={"marginBottom":"20px"}),
                    html.Button("Créer le compte", id="btn-gc-create",
                                className="btn-sga btn-gold",
                                style={"width":"100%","justifyContent":"center"}),
                    html.Div(id="gc-feedback", style={"marginTop":"12px"}),
                ], className="sga-card"),
            ], style={"width":"320px","flexShrink":"0"}),

            # Liste comptes
            html.Div([
                html.Div([
                    html.Div("Comptes existants", className="sga-card-title",
                             style={"marginBottom":"20px"}),
                    html.Div(id="gc-list"),
                ], className="sga-card"),
            ], style={"flex":"1"}),
        ], style={"display":"flex","gap":"24px","alignItems":"flex-start"}),

        dcc.Store(id="gc-refresh", data=0),
    ])


@callback(
    Output("gc-feedback","children"),
    Output("gc-refresh","data"),
    Input("btn-gc-create","n_clicks"),
    State("gc-role","value"),
    State("gc-user","value"),
    State("gc-pass","value"),
    State("gc-linked","value"),
    State("gc-refresh","data"),
    prevent_initial_call=True,
)
def creer_compte(n, role, username, pwd, linked_id, refresh):
    if not role or not username or not pwd:
        return html.Div("Rôle, identifiant et mot de passe requis.",
                        className="sga-alert sga-alert-warning"), dash.no_update
    db = SessionLocal()
    try:
        existing = db.query(User).filter_by(username=username).first()
        if existing:
            return html.Div(f"L\'identifiant «{username}» existe déjà.",
                            className="sga-alert sga-alert-danger"), dash.no_update
        u = User(username=username,
                 password_hash=generate_password_hash(pwd),
                 role=role, linked_id=linked_id,
                 created_at=datetime.now())
        db.add(u); db.commit()
        return html.Div(f"✓ Compte «{username}» ({role}) créé.",
                        className="sga-alert sga-alert-success"), (refresh or 0) + 1
    except Exception as e:
        db.rollback()
        return html.Div(str(e), className="sga-alert sga-alert-danger"), dash.no_update
    finally:
        db.close()


@callback(Output("gc-list","children"), Input("gc-refresh","data"))
def lister_comptes(refresh):
    db = SessionLocal()
    try:
        users = db.query(User).order_by(User.role, User.username).all()
        students = {s.id: f"{s.nom} {s.prenom}"
                    for s in db.query(Student).all()}
    finally:
        db.close()

    if not users:
        return html.Div("Aucun compte créé.",
                        style={"color":"var(--muted)","textAlign":"center","padding":"40px"})

    cards = []
    for u in users:
        col   = ROLE_COLORS.get(u.role, "var(--muted)")
        icon  = ROLE_ICONS.get(u.role, "◆")
        linked= f" → {students[u.linked_id]}" if u.linked_id and u.linked_id in students else ""
        cards.append(html.Div([
            html.Div([
                html.Span(icon, style={"color":col,"fontSize":"18px","marginRight":"10px"}),
                html.Span(u.username, style={"fontWeight":"700","fontSize":"15px"}),
            ], style={"display":"flex","alignItems":"center","marginBottom":"6px"}),
            html.Div(u.role.upper(),
                     style={"fontSize":"9px","letterSpacing":"3px",
                            "color":col,"marginBottom":"4px"}),
            html.Div(linked, style={"fontSize":"12px","color":"var(--muted)"}),
        ], style={"padding":"16px","background":"var(--bg-secondary)",
                  "borderRadius":"4px","marginBottom":"8px",
                  "borderLeft":f"3px solid {col}"}))
    return html.Div(cards)
