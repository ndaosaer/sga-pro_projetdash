import dash
from dash import html, dcc, Input, Output, State, callback, ctx
from database import SessionLocal
from models import Course, Session

dash.register_page(__name__, path="/cours", name="Cours")

COULEURS = [
    {"label": "Or",        "value": "#C9A84C"},
    {"label": "Platine",   "value": "#E8E0D0"},
    {"label": "Ambre",     "value": "#D4A017"},
    {"label": "Cuivre",    "value": "#B87333"},
    {"label": "Argent",    "value": "#A8A9AD"},
    {"label": "Ivoire",    "value": "#F5F0E8"},
]

def layout():
    return html.Div([
        html.Div([
            html.Div([html.Div("Gestion des Cours", className="page-title"),
                      html.Div("Curriculum — CRUD et suivi de progression", className="page-subtitle")]),
            html.Button("+ Nouveau cours", id="btn-open-form", className="btn-sga btn-gold"),
        ], className="topbar"),

        html.Div([
            html.Div([
                html.Div("Enregistrement d un cours", className="sga-card-title", style={"marginBottom":"20px"}),
                html.Div([
                    html.Div([html.Span("Code", className="sga-label"),
                              dcc.Input(id="inp-code", placeholder="MATH101", className="sga-input", style={"width":"100%"})]),
                    html.Div([html.Span("Libelle", className="sga-label"),
                              dcc.Input(id="inp-lib", placeholder="Mathematiques Avancees", className="sga-input", style={"width":"100%"})]),
                    html.Div([html.Span("Volume horaire (h)", className="sga-label"),
                              dcc.Input(id="inp-vol", type="number", placeholder="60", className="sga-input", style={"width":"100%"})]),
                    html.Div([html.Span("Enseignant", className="sga-label"),
                              dcc.Input(id="inp-ens", placeholder="Dr. Dupont", className="sga-input", style={"width":"100%"})]),
                    html.Div([html.Span("Couleur", className="sga-label"),
                              dcc.Dropdown(id="inp-col", options=COULEURS, value="#C9A84C",
                                           clearable=False, style={"fontSize":"12px"})]),
                ], style={"display":"grid","gridTemplateColumns":"1fr 2fr 1fr 1.5fr 1fr","gap":"16px","marginBottom":"16px"}),
                html.Div([
                    html.Button("Sauvegarder", id="btn-save-c", className="btn-sga btn-gold"),
                    html.Button("Annuler",     id="btn-cancel-c", className="btn-sga btn-danger", style={"marginLeft":"10px"}),
                ]),
                html.Div(id="fb-course"),
            ], className="sga-card"),
        ], id="form-wrap", style={"display":"none","marginBottom":"24px"}),

        html.Div(id="grid-courses"),
        dcc.Interval(id="iv-cours", interval=3000, max_intervals=1),
    ])

@callback(Output("form-wrap","style"),
          Input("btn-open-form","n_clicks"), Input("btn-cancel-c","n_clicks"),
          prevent_initial_call=True)
def toggle_form(o, c):
    return {"display":"block","marginBottom":"24px"} if ctx.triggered_id == "btn-open-form" else {"display":"none","marginBottom":"24px"}

@callback(Output("fb-course","children"), Output("grid-courses","children", allow_duplicate=True),
          Input("btn-save-c","n_clicks"),
          State("inp-code","value"), State("inp-lib","value"), State("inp-vol","value"),
          State("inp-ens","value"),  State("inp-col","value"),
          prevent_initial_call=True)
def save_course(n, code, lib, vol, ens, col):
    if not all([code, lib, vol]):
        return _alert("Code, libelle et volume sont obligatoires.", "warning"), build_grid()
    db = SessionLocal()
    try:
        ex = db.get(Course, code)
        if ex:
            ex.libelle = lib; ex.volume_horaire = float(vol)
            ex.enseignant = ens; ex.couleur = col or "#C9A84C"
            msg = _alert(f"Cours {code} mis a jour.", "success")
        else:
            db.add(Course(code=code, libelle=lib, volume_horaire=float(vol), enseignant=ens, couleur=col or "#C9A84C"))
            msg = _alert(f"Cours {code} cree.", "success")
        db.commit()
    except Exception as e:
        db.rollback(); msg = _alert(str(e), "danger")
    finally:
        db.close()
    return msg, build_grid()

@callback(Output("grid-courses","children"), Input("iv-cours","n_intervals"))
def load_grid(_): return build_grid()

def build_grid():
    db = SessionLocal()
    courses  = db.query(Course).all()
    sessions = db.query(Session).all()
    course_data = []
    for c in courses:
        heures = round(sum(s.duree for s in sessions if s.course_code == c.code), 1)
        prog   = min(round(heures / c.volume_horaire * 100, 1), 100) if c.volume_horaire else 0
        nb_s   = sum(1 for s in sessions if s.course_code == c.code)
        course_data.append({
            "code": c.code, "libelle": c.libelle, "enseignant": c.enseignant or "---",
            "volume": c.volume_horaire, "heures": heures, "prog": prog,
            "nb_sessions": nb_s, "couleur": c.couleur or "#C9A84C",
        })
    db.close()

    if not course_data:
        return html.Div("Aucun cours enregistre.", style={"color":"var(--text-muted)","textAlign":"center","padding":"40px"})

    cards = []
    for c in course_data:
        prog  = c["prog"]
        color = c["couleur"]
        status = "Termine" if prog >= 100 else "En cours" if prog > 0 else "Planifie"
        sc = "tag-gold" if prog >= 100 else "tag-silver" if prog >= 50 else "tag-copper"
        cards.append(html.Div([
            html.Div([
                html.Span(c["code"], style={"color":color,"fontWeight":"700","fontSize":"13px","letterSpacing":"2px","fontFamily":"'JetBrains Mono',monospace"}),
                html.Span(status, className=f"tag {sc}", style={"marginLeft":"auto"}),
            ], style={"display":"flex","alignItems":"center","marginBottom":"8px"}),
            html.Div(c["libelle"], style={"fontSize":"16px","fontFamily":"'Cormorant Garamond',serif",
                                          "fontWeight":"600","marginBottom":"4px","color":"var(--text-primary)"}),
            html.Div(c["enseignant"], style={"color":"var(--text-muted)","fontSize":"11px","marginBottom":"16px","letterSpacing":"1px"}),
            html.Div([
                html.Div(f"{c['heures']}h / {c['volume']}h",
                         style={"fontSize":"11px","color":"var(--text-muted)","marginBottom":"6px"}),
                html.Div(html.Div(style={
                    "width": f"{prog}%",
                    "background": f"linear-gradient(90deg, {color}, #E8E0D0)",
                    "height": "100%", "borderRadius": "4px", "transition": "width 0.8s",
                }), className="sga-progress-wrap"),
                html.Div(f"{prog}%", style={"fontSize":"11px","color":color,"textAlign":"right","marginTop":"4px","fontFamily":"'JetBrains Mono',monospace"}),
            ]),
            html.Div(f"{c['nb_sessions']} seance(s)",
                     style={"fontSize":"10px","color":"var(--text-muted)","marginTop":"12px","letterSpacing":"1px"}),
        ], className="sga-card", style={"borderTop":f"2px solid {color}"}))

    return html.Div(cards, style={"display":"grid","gridTemplateColumns":"repeat(auto-fill,minmax(280px,1fr))","gap":"20px"})

def _alert(msg, t):
    cls = {"success":"sga-alert-success","warning":"sga-alert-warning","danger":"sga-alert-danger"}
    return html.Div(msg, className=f"sga-alert {cls.get(t,'sga-alert-info')}")
