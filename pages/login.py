import dash
from dash import html, dcc, Input, Output, State, callback
from werkzeug.security import check_password_hash
from database import SessionLocal
from models import User

dash.register_page(__name__, path="/login", name="Login")

def layout():
    return html.Div([
        html.Div([
            html.Div("Nafa Scolaire", className="login-title"),
            html.Div("Systeme de Gestion Academique", className="login-subtitle"),
            html.Div([
                html.Span("Identifiant", className="sga-label"),
                dcc.Input(id="l-user", placeholder="admin", className="sga-input",
                          style={"width":"100%","marginBottom":"16px"}),
                html.Span("Mot de passe", className="sga-label"),
                dcc.Input(id="l-pass", type="password", placeholder="........", className="sga-input",
                          style={"width":"100%","marginBottom":"24px"}),
                html.Button("CONNEXION", id="btn-login", className="btn-sga btn-cyan",
                            style={"width":"100%","justifyContent":"center","fontSize":"13px"}),
                html.Div(id="l-fb", style={"marginTop":"12px"}),
                dcc.Location(id="l-redir"),
            ]),
        ], className="login-box"),
    ], className="login-page")

@callback(Output("l-fb","children"), Output("l-redir","pathname"),
          Input("btn-login","n_clicks"), State("l-user","value"), State("l-pass","value"),
          prevent_initial_call=True)
def do_login(n,user,pwd):
    if not user or not pwd:
        return html.Div("Identifiant et mot de passe requis.", className="sga-alert sga-alert-warning"), dash.no_update
    db = SessionLocal()
    u = db.query(User).filter_by(username=user).first()
    db.close()
    if u and check_password_hash(u.password_hash, pwd):
        return html.Div("Connexion reussie.", className="sga-alert sga-alert-success"), "/"
    return html.Div("Identifiants invalides.", className="sga-alert sga-alert-danger"), dash.no_update
