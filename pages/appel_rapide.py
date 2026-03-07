import dash
from dash import html, dcc, Input, Output, State, callback, ALL, ctx
from database import SessionLocal
from models import Course, Student, Session, Attendance
from datetime import date, datetime

dash.register_page(__name__, path="/appel", name="Appel Rapide")

def layout():
    db = SessionLocal()
    cours_opts = [{"label": f"{c.code} — {c.libelle}", "value": c.code}
                  for c in db.query(Course).all()]
    db.close()

    return html.Div([
        # TOPBAR
        html.Div([
            html.Div([
                html.Div("Appel Rapide", className="page-title"),
                html.Div("Saisie en moins de 10 secondes", className="page-subtitle"),
            ]),
            html.Div(date.today().strftime("%A %d %B %Y").capitalize(),
                     style={"fontFamily":"'JetBrains Mono',monospace",
                            "color":"var(--gold)","fontSize":"13px","letterSpacing":"2px"}),
        ], className="topbar"),

        # ETAPE 1 — Choisir le cours
        html.Div([
            html.Div([
                html.Div("① Sélectionner le cours", className="sga-card-title",
                         style={"marginBottom":"16px"}),
                html.Div([
                    dcc.Dropdown(
                        id="ar-cours",
                        options=cours_opts,
                        placeholder="Choisir le cours…",
                        clearable=False,
                        style={"flex":"1","minWidth":"260px","fontSize":"13px"},
                    ),
                    dcc.Input(id="ar-duree", type="number", placeholder="Durée (h)",
                              min=0.5, step=0.5, value=2.0,
                              className="sga-input",
                              style={"width":"140px","flexShrink":"0"}),
                    dcc.Input(id="ar-theme", placeholder="Thème du cours (optionnel)",
                              className="sga-input", style={"flex":"1"}),
                ], style={"display":"flex","gap":"12px","alignItems":"center"}),
            ], className="sga-card"),
        ], style={"marginBottom":"20px"}),

        # ETAPE 2 — Liste d'appel
        html.Div(id="ar-appel-zone"),

        # RESULTAT
        html.Div(id="ar-result"),

    ], style={"maxWidth":"700px","margin":"0 auto"})


@callback(
    Output("ar-appel-zone", "children"),
    Input("ar-cours", "value"),
    prevent_initial_call=True,
)
def afficher_appel(code):
    if not code:
        return ""
    db = SessionLocal()
    students = [(s.id, s.nom, s.prenom)
                for s in db.query(Student).filter_by(actif=True).order_by(Student.nom).all()]
    # Stats absences existantes pour ce cours
    sessions = db.query(Session).filter_by(course_code=code).all()
    sess_ids = [s.id for s in sessions]
    abs_counts = {}
    for sid, nom, prenom in students:
        abs_counts[sid] = sum(
            1 for a in db.query(Attendance).filter_by(id_student=sid).all()
            if a.id_session in sess_ids
        )
    total_sess = len(sessions)
    db.close()

    return html.Div([
        html.Div([
            html.Div("② Faire l'appel — Cocher les absents", className="sga-card-title",
                     style={"marginBottom":"4px"}),
            html.Div(f"{len(students)} étudiants · {total_sess} séances déjà enregistrées",
                     style={"fontSize":"12px","color":"var(--muted)","fontFamily":"'JetBrains Mono',monospace",
                            "marginBottom":"20px"}),

            # Boutons rapides
            html.Div([
                html.Button("Tout présent ✓", id="ar-tout-present",
                            className="btn-sga btn-green",
                            style={"fontSize":"12px","padding":"8px 16px"}),
                html.Button("Tout absent ✗", id="ar-tout-absent",
                            className="btn-sga btn-danger",
                            style={"fontSize":"12px","padding":"8px 16px"}),
            ], style={"display":"flex","gap":"10px","marginBottom":"20px"}),

            # Liste étudiants — cartes cliquables
            html.Div([
                _carte_etudiant(sid, nom, prenom, abs_counts.get(sid, 0), total_sess)
                for sid, nom, prenom in students
            ], id="ar-liste",
               style={"display":"grid","gridTemplateColumns":"1fr 1fr","gap":"10px",
                      "marginBottom":"24px"}),

            # Bouton valider
            html.Button("✓ Valider l'appel", id="ar-valider",
                        className="btn-sga btn-gold",
                        style={"width":"100%","justifyContent":"center",
                               "fontSize":"14px","padding":"14px","letterSpacing":"3px"}),
            html.Div(id="ar-result"),
        ], className="sga-card"),

        # Store pour les absents sélectionnés
        dcc.Store(id="ar-absents-store", data=[]),
    ], style={"marginBottom":"20px"})


def _carte_etudiant(sid, nom, prenom, nb_abs, total_sess):
    taux = round(nb_abs / total_sess * 100) if total_sess else 0
    danger = taux >= 20
    couleur_abs = "var(--red)" if danger else "var(--copper)" if taux >= 10 else "var(--green)"
    return html.Div([
        html.Div([
            html.Div(f"{nom[0]}{prenom[0]}", style={
                "width":"38px","height":"38px","borderRadius":"8px","flexShrink":"0",
                "background":"linear-gradient(135deg,var(--gold-dim),var(--gold))",
                "display":"flex","alignItems":"center","justifyContent":"center",
                "fontSize":"14px","fontWeight":"700","color":"var(--bg-primary)",
                "fontFamily":"'Times New Roman',serif",
            }),
            html.Div([
                html.Div(f"{nom} {prenom}",
                         style={"fontSize":"14px","fontWeight":"600","color":"var(--text-primary)"}),
                html.Div(f"{nb_abs} abs. ({taux}%)",
                         style={"fontSize":"11px","color":couleur_abs,
                                "fontFamily":"'JetBrains Mono',monospace"}),
            ]),
        ], style={"display":"flex","gap":"10px","alignItems":"center"}),
    ],
    id={"type":"ar-etu","index":sid},
    n_clicks=0,
    style={
        "padding":"12px 14px","borderRadius":"6px","cursor":"pointer",
        "border":"1px solid var(--border)","background":"var(--bg-card)",
        "transition":"all 0.15s","userSelect":"none",
    })


@callback(
    Output({"type":"ar-etu","index":ALL}, "style"),
    Output("ar-absents-store", "data"),
    Input({"type":"ar-etu","index":ALL}, "n_clicks"),
    Input("ar-tout-present", "n_clicks"),
    Input("ar-tout-absent", "n_clicks"),
    State({"type":"ar-etu","index":ALL}, "id"),
    State("ar-absents-store", "data"),
    prevent_initial_call=True,
)
def toggle_absent(clicks, btn_present, btn_absent, ids, absents):
    triggered = ctx.triggered_id

    # Bouton tout présent
    if triggered == "ar-tout-present":
        absents = []
    # Bouton tout absent
    elif triggered == "ar-tout-absent":
        absents = [i["index"] for i in ids]
    # Clic sur une carte
    elif isinstance(triggered, dict) and triggered.get("type") == "ar-etu":
        sid = triggered["index"]
        if sid in absents:
            absents = [x for x in absents if x != sid]
        else:
            absents = absents + [sid]

    styles = []
    for id_obj in ids:
        sid = id_obj["index"]
        if sid in absents:
            styles.append({
                "padding":"12px 14px","borderRadius":"6px","cursor":"pointer",
                "border":"2px solid var(--red)","background":"rgba(139,37,0,0.08)",
                "transition":"all 0.15s","userSelect":"none",
                "boxShadow":"0 0 0 3px rgba(139,37,0,0.1)",
            })
        else:
            styles.append({
                "padding":"12px 14px","borderRadius":"6px","cursor":"pointer",
                "border":"1px solid var(--border)","background":"var(--bg-card)",
                "transition":"all 0.15s","userSelect":"none",
            })
    return styles, absents


@callback(
    Output("ar-result", "children"),
    Input("ar-valider", "n_clicks"),
    State("ar-cours", "value"),
    State("ar-duree", "value"),
    State("ar-theme", "value"),
    State("ar-absents-store", "data"),
    prevent_initial_call=True,
)
def valider_appel(n, code, duree, theme, absents):
    if not code or not duree:
        return html.Div("Sélectionnez un cours et une durée.",
                        className="sga-alert sga-alert-warning")
    db = SessionLocal()
    try:
        sess = Session(
            course_code=code,
            date=date.today(),
            duree=float(duree),
            theme=theme or "",
        )
        db.add(sess); db.flush()
        for sid in (absents or []):
            db.add(Attendance(id_session=sess.id, id_student=sid))
        db.commit()
        nb_abs = len(absents or [])
        return html.Div([
            html.Div("✓ Séance enregistrée !", style={
                "fontFamily":"'Times New Roman',serif","fontSize":"20px",
                "fontWeight":"700","color":"var(--green)","marginBottom":"8px",
            }),
            html.Div(
                f"Cours {code} · {duree}h · {nb_abs} absent(s) · {date.today().strftime('%d/%m/%Y')}",
                style={"fontFamily":"'JetBrains Mono',monospace","fontSize":"12px",
                       "color":"var(--muted)"},
            ),
        ], className="sga-alert sga-alert-success", style={"marginTop":"16px"})
    except Exception as e:
        db.rollback()
        return html.Div(str(e), className="sga-alert sga-alert-danger")
    finally:
        db.close()
