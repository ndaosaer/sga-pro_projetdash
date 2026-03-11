import dash
from dash import html, dcc, Input, Output, callback
from database import SessionLocal
from models import Student, Course, Session, Attendance, Grade, Notification
from datetime import date, timedelta

dash.register_page(__name__, path="/alertes", name="Alertes")

SEUIL_ABSENCE  = 20   # % maxi tolere
SEUIL_MOYENNE  = 10   # note mini requise
SEUIL_INACTIF  = 14   # jours sans seance

def _detecter_alertes():
    """Analyse la BDD et retourne la liste des alertes detectees."""
    db = SessionLocal()
    alertes = []
    try:
        students    = db.query(Student).filter_by(actif=True).all()
        courses     = db.query(Course).all()
        sessions    = db.query(Session).all()
        attendances = db.query(Attendance).all()
        grades      = db.query(Grade).all()
        today       = date.today()

        for course in courses:
            c_sessions = [s for s in sessions if s.course_code == course.code]
            nb_sess    = len(c_sessions)

            # ── ALERTE 3 : Cours inactif depuis 2 semaines ──────────────────
            if c_sessions:
                last_date = max(s.date for s in c_sessions)
                jours = (today - last_date).days
                if jours >= SEUIL_INACTIF:
                    alertes.append({
                        "type":    "inactif",
                        "niveau":  "warning",
                        "titre":   f"Cours inactif — {course.code}",
                        "detail":  f"Aucune séance depuis {jours} jours ({last_date.strftime('%d/%m/%Y')})",
                        "cours":   course.libelle,
                        "icone":   "⏸",
                    })

            if nb_sess == 0:
                continue

            sess_ids = {s.id for s in c_sessions}

            for student in students:
                # Absences de cet étudiant dans ce cours
                nb_abs = sum(1 for a in attendances
                             if a.id_session in sess_ids and a.id_student == student.id)
                taux   = round(nb_abs / nb_sess * 100, 1)

                # Moyenne de cet étudiant dans ce cours
                g = [gr for gr in grades
                     if gr.id_student == student.id and gr.course_code == course.code]
                tc  = sum(gr.coefficient for gr in g)
                moy = round(sum(gr.note * gr.coefficient for gr in g) / tc, 2) if tc else None

                # ── ALERTE 1 : Absence excessive ────────────────────────────
                if taux > SEUIL_ABSENCE:
                    alertes.append({
                        "type":    "absence",
                        "niveau":  "danger" if taux > 30 else "warning",
                        "titre":   f"{student.nom} {student.prenom} — {course.code}",
                        "detail":  f"Taux d'absence : {taux}% ({nb_abs}/{nb_sess} séances)",
                        "cours":   course.libelle,
                        "icone":   "" if taux > 30 else "",
                    })

                # ── ALERTE 2 : Moyenne en danger ────────────────────────────
                if moy is not None and moy < SEUIL_MOYENNE:
                    alertes.append({
                        "type":    "moyenne",
                        "niveau":  "danger" if moy < 8 else "warning",
                        "titre":   f"{student.nom} {student.prenom} — {course.code}",
                        "detail":  f"Moyenne : {moy}/20 (seuil minimum : {SEUIL_MOYENNE}/20)",
                        "cours":   course.libelle,
                        "icone":   "" if moy < 8 else "",
                    })

    finally:
        db.close()

    # Trier : dangers d'abord, puis warnings
    alertes.sort(key=lambda a: (0 if a["niveau"] == "danger" else 1, a["type"]))
    return alertes


def _sauvegarder_notifications(alertes):
    """Enregistre les nouvelles alertes en base (sans doublons)."""
    db = SessionLocal()
    try:
        existantes = {n.titre for n in db.query(Notification).all()}
        for a in alertes:
            if a["titre"] not in existantes:
                db.add(Notification(
                    type=a["niveau"],
                    titre=a["titre"],
                    message=a["detail"],
                    lu=False,
                ))
        db.commit()
    finally:
        db.close()


def layout():
    return html.Div([
        html.Div([
            html.Div([
                html.Div("Alertes Intelligentes", className="page-title"),
                html.Div("Surveillance automatique de la promotion", className="page-subtitle"),
            ]),
            html.Button(" Actualiser", id="btn-refresh-alertes",
                        className="btn-sga btn-gold"),
        ], className="topbar"),

        # Seuils configurables
        html.Div([
            html.Div([
                html.Div("Paramètres de détection", className="sga-card-title",
                         style={"marginBottom":"16px"}),
                html.Div([
                    html.Div([
                        html.Span("Seuil absence (%)", className="sga-label"),
                        dcc.Input(id="seuil-abs", type="number", value=SEUIL_ABSENCE,
                                  min=5, max=50, step=5, className="sga-input",
                                  style={"width":"100%"}),
                    ]),
                    html.Div([
                        html.Span("Seuil moyenne (/20)", className="sga-label"),
                        dcc.Input(id="seuil-moy", type="number", value=SEUIL_MOYENNE,
                                  min=5, max=15, step=1, className="sga-input",
                                  style={"width":"100%"}),
                    ]),
                    html.Div([
                        html.Span("Inactivité (jours)", className="sga-label"),
                        dcc.Input(id="seuil-inactif", type="number", value=SEUIL_INACTIF,
                                  min=7, max=60, step=7, className="sga-input",
                                  style={"width":"100%"}),
                    ]),
                    html.Div([
                        html.Span(" ", className="sga-label"),
                        html.Button("Appliquer", id="btn-appliquer-seuils",
                                    className="btn-sga btn-gold",
                                    style={"width":"100%","justifyContent":"center"}),
                    ]),
                ], style={"display":"grid","gridTemplateColumns":"1fr 1fr 1fr 1fr","gap":"16px"}),
            ], className="sga-card"),
        ], style={"marginBottom":"24px"}),

        # Résumé en KPIs
        html.Div(id="alertes-kpis", style={"marginBottom":"24px"}),

        # Liste des alertes
        html.Div(id="alertes-liste"),

        dcc.Interval(id="iv-alertes", interval=120000),  # refresh toutes les 2min
        dcc.Store(id="store-seuils", data={
            "abs": SEUIL_ABSENCE, "moy": SEUIL_MOYENNE, "inactif": SEUIL_INACTIF
        }),
    ])


@callback(
    Output("store-seuils", "data"),
    Input("btn-appliquer-seuils", "n_clicks"),
    dash.dependencies.State("seuil-abs", "value"),
    dash.dependencies.State("seuil-moy", "value"),
    dash.dependencies.State("seuil-inactif", "value"),
    prevent_initial_call=True,
)
def maj_seuils(n, abs_v, moy_v, inactif_v):
    return {"abs": abs_v or 20, "moy": moy_v or 10, "inactif": inactif_v or 14}


@callback(
    Output("alertes-kpis",  "children"),
    Output("alertes-liste", "children"),
    Input("iv-alertes", "n_intervals"),
    Input("btn-refresh-alertes", "n_clicks"),
    Input("store-seuils", "data"),
)
def afficher_alertes(_, __, seuils):
    global SEUIL_ABSENCE, SEUIL_MOYENNE, SEUIL_INACTIF
    SEUIL_ABSENCE = seuils.get("abs", 20)
    SEUIL_MOYENNE = seuils.get("moy", 10)
    SEUIL_INACTIF = seuils.get("inactif", 14)

    alertes = _detecter_alertes()
    _sauvegarder_notifications(alertes)

    nb_danger  = sum(1 for a in alertes if a["niveau"] == "danger")
    nb_warning = sum(1 for a in alertes if a["niveau"] == "warning")
    nb_absence = sum(1 for a in alertes if a["type"] == "absence")
    nb_moyenne = sum(1 for a in alertes if a["type"] == "moyenne")
    nb_inactif = sum(1 for a in alertes if a["type"] == "inactif")

    # ── KPIs ──
    kpis = html.Div([
        _kpi(str(len(alertes)), "Alertes totales",    "kpi-copper"),
        _kpi(str(nb_danger),   "Niveau critique 🔴",  "kpi-red"),
        _kpi(str(nb_warning),  "Niveau attention 🟠", "kpi-orange"),
        _kpi(str(nb_absence),  "Absences excessives", "kpi-cyan"),
        _kpi(str(nb_moyenne),  "Moyennes faibles",    "kpi-purple"),
    ], style={"display":"grid","gridTemplateColumns":"repeat(5,1fr)","gap":"16px"})

    # ── LISTE ──
    if not alertes:
        liste = html.Div([
            html.Div("✓", style={"fontSize":"64px","color":"var(--green)",
                                  "textAlign":"center","marginBottom":"16px"}),
            html.Div("Aucune alerte détectée", style={
                "textAlign":"center","fontSize":"22px","fontFamily":"'Times New Roman',serif",
                "fontWeight":"700","color":"var(--text-primary)","marginBottom":"8px",
            }),
            html.Div("Tous les étudiants sont dans les seuils définis.",
                     style={"textAlign":"center","color":"var(--muted)","fontSize":"14px"}),
        ], className="sga-card", style={"padding":"48px"})
    else:
        # Grouper par type
        sections = [
            ("absence", " Absences excessives",      "var(--red)"),
            ("moyenne", " Moyennes insuffisantes",    "var(--copper)"),
            ("inactif", "⏸ Cours inactifs",             "var(--gold)"),
        ]
        blocs = []
        for type_key, titre_section, couleur in sections:
            items = [a for a in alertes if a["type"] == type_key]
            if not items:
                continue
            blocs.append(html.Div([
                html.Div(titre_section, style={
                    "fontFamily":"'Times New Roman',serif","fontSize":"20px",
                    "fontWeight":"700","color":couleur,"marginBottom":"14px",
                    "paddingBottom":"10px","borderBottom":"1px solid var(--border)",
                }),
                html.Div([_carte_alerte(a) for a in items],
                         style={"display":"flex","flexDirection":"column","gap":"10px"}),
            ], className="sga-card", style={"marginBottom":"20px",
                                             "borderTop":f"3px solid {couleur}"}))
        liste = html.Div(blocs)

    return kpis, liste


def _kpi(val, label, cls):
    return html.Div([
        html.Div(val,   className="kpi-value"),
        html.Div(label, className="kpi-label"),
    ], className=f"kpi-card {cls}")


def _carte_alerte(a):
    couleurs = {
        "danger":  ("rgba(139,37,0,0.08)",  "rgba(139,37,0,0.3)",  "var(--red)"),
        "warning": ("rgba(155,94,42,0.08)", "rgba(155,94,42,0.3)", "var(--copper)"),
    }
    bg, border, text = couleurs.get(a["niveau"], couleurs["warning"])
    return html.Div([
        html.Div([
            html.Span(a["icone"], style={"fontSize":"22px","flexShrink":"0"}),
            html.Div([
                html.Div(a["titre"], style={
                    "fontFamily":"'Times New Roman',serif","fontSize":"16px",
                    "fontWeight":"700","color":"var(--text-primary)","marginBottom":"4px",
                }),
                html.Div(a["detail"], style={
                    "fontSize":"13px","color":"var(--muted)",
                    "fontFamily":"'JetBrains Mono',monospace",
                }),
                html.Div(a["cours"], style={
                    "fontSize":"11px","color":text,"marginTop":"6px",
                    "fontFamily":"'JetBrains Mono',monospace","letterSpacing":"1px",
                }),
            ]),
            html.Span("CRITIQUE" if a["niveau"] == "danger" else "ATTENTION",
                      style={
                          "marginLeft":"auto","flexShrink":"0",
                          "fontSize":"9px","letterSpacing":"2px","fontWeight":"700",
                          "fontFamily":"'JetBrains Mono',monospace",
                          "color":text,"border":f"1px solid {border}",
                          "background":bg,"padding":"4px 10px","borderRadius":"2px",
                      }),
        ], style={"display":"flex","gap":"14px","alignItems":"flex-start"}),
    ], style={
        "padding":"16px 20px","borderRadius":"4px",
        "background":bg,"border":f"1px solid {border}",
    })
