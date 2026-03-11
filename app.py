import dash
from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
from components.sidebar import create_sidebar

app = Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    title="Nafa Scolaire",
    update_title=None,
)
server = app.server

# ── Init base de données au démarrage (Gunicorn + local) ──
from database import init_db, init_users
try:
    init_db()
    init_users()
except Exception as _e:
    print(f"Init DB warning: {_e}")


import json as _json
from flask import request as _request

@server.route("/webhook/paytech", methods=["POST"])
def paytech_webhook():
    """Reçoit la notification Paytech après paiement réussi."""
    try:
        data = _request.form.to_dict() or _request.get_json() or {}
        ref          = data.get("ref_command","")
        type_cmd     = data.get("command_name","")
        montant      = float(data.get("item_price", 0))
        custom_raw   = data.get("custom_field","{}") or "{}"
        custom       = _json.loads(custom_raw) if isinstance(custom_raw, str) else custom_raw
        type_pay     = custom.get("type","")

        from database import SessionLocal
        from models import Paiement, Candidat, Student, FraisScolarite
        from datetime import datetime

        db = SessionLocal()
        try:
            if type_pay == "scolarite":
                email = custom.get("email","")
                stu = db.query(Student).filter_by(email=email).first()
                if stu:
                    p = Paiement()
                    p.student_id    = stu.id
                    p.montant       = montant
                    p.mode_paiement = "Paytech (mobile money)"
                    p.reference     = ref
                    p.date_paiement = datetime.now()
                    p.valide        = True
                    p.annee         = "2025-2026"
                    db.add(p); db.commit()

            elif type_pay == "concours":
                nom    = custom.get("nom","")
                prenom = custom.get("prenom","")
                email  = custom.get("email","")
                cand = db.query(Candidat).filter_by(email=email).first()
                if cand:
                    cand.paiement_statut = "paye"
                    cand.reference_paiement = ref
                    db.commit()
        finally:
            db.close()

        return {"status": "ok"}, 200
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500


PUBLIC_PATHS = {"/accueil", "/auth", "/login", "/concours"}

ROLE_ROUTES = {
    "/admin-concours":    ["admin"],
    "/concours":          [],          # public — tous les connectes
    "/portail-etudiant":   ["student"],
    "/portail-parent":     ["parent"],
    "/portail-secretaire": ["secretary"],
    "/gestion-comptes":    ["admin"],
    "/classes":            ["admin"],
    "/direction":          ["admin"],
    "/rapports":           ["admin"],
    "/paiements":          ["admin","teacher"],
    "/messagerie":         [],
    "/emploi-du-temps":    ["admin","teacher","student","secretary"],
    "/paiement-en-ligne":  [],
    "/paiement-succes":    [],
    "/paiement-annule":    [],
    "/bulletin":           ["admin","teacher","student"],
    "/alertes":            ["admin","teacher"],
    "/comparateur":        ["admin","teacher"],
    "/analytics":          ["admin","teacher"],
    "/calendrier":         ["admin","teacher","secretary"],
    "/appel":              ["admin","teacher"],
    "/presences":          ["admin","teacher"],
    "/cours":              ["admin","teacher"],
    "/etudiants":          ["admin","teacher"],
}

SIDEBAR_ROLES = {"admin","teacher","secretary","student","parent"}
NO_SIDEBAR    = set()  # tous les roles connectes ont la sidebar

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dcc.Store(id="session-store", storage_type="session"),
    html.Div(id="app-shell"),
])

@app.callback(
    Output("app-shell","children"),
    Input("url","pathname"),
    Input("session-store","data"),
)
def render_shell(path, session):
    path = path or "/"

    if path in PUBLIC_PATHS:
        return html.Div(dcc.Loading(id="global-loading", type="circle", color="#B8922A",
                     fullscreen=False, delay_show=200,
                     children=dash.page_container), style={"minHeight":"100vh"})

    if not session or not session.get("logged_in"):
        return dcc.Location(href="/auth", id="redir-auth")

    role     = session.get("role","")
    username = session.get("username","")

    if path in ROLE_ROUTES and ROLE_ROUTES[path] and role not in ROLE_ROUTES[path]:
        return html.Div([
            html.Div([
                html.Div("", style={"fontSize":"64px","textAlign":"center","marginBottom":"16px"}),
                html.Div("Accès non autorisé",
                         style={"fontFamily":"Times New Roman,serif","fontSize":"32px",
                                "fontWeight":"700","textAlign":"center",
                                "color":"var(--red)","marginBottom":"8px"}),
                html.Div(f"Cette page est réservée aux rôles : {', '.join(ROLE_ROUTES[path])}",
                         style={"textAlign":"center","color":"var(--muted)","fontSize":"14px",
                                "marginBottom":"24px"}),
                html.Div(dcc.Link("← Retour", href="/",
                         style={"color":"var(--gold)","textDecoration":"none"}),
                         style={"textAlign":"center"}),
            ], style={"maxWidth":"480px","margin":"120px auto","padding":"48px",
                      "background":"var(--bg-card)","border":"1px solid var(--border)",
                      "borderRadius":"6px"}),
        ])

    if path in NO_SIDEBAR:
        return html.Div(dcc.Loading(id="global-loading", type="circle", color="#B8922A",
                     fullscreen=False, delay_show=200,
                     children=dash.page_container), style={"minHeight":"100vh"})

    if role in SIDEBAR_ROLES:
        return html.Div([
            create_sidebar(role=role, username=username),
            html.Div(dcc.Loading(id="global-loading", type="circle", color="#B8922A",
                     fullscreen=False, delay_show=200,
                     children=dash.page_container), className="main-content"),
        ], style={"minHeight":"100vh"})

    return dcc.Location(href="/auth", id="redir-fb")


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8050))
    debug = os.environ.get("RAILWAY_ENVIRONMENT") is None
    import threading, webbrowser
    threading.Timer(1.5, lambda: webbrowser.open("http://127.0.0.1:8050/accueil")).start()
    app.run(debug=False)
