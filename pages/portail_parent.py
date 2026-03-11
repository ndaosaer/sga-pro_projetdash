import dash
from dash import html, dcc, Input, Output, State, callback
from database import SessionLocal
from models import Student, Grade, Course, Session as Sess, Attendance, Notification
from models import Classe, Creneau, User
import plotly.graph_objects as go
from datetime import date, timedelta

dash.register_page(__name__, path="/portail-parent", name="Suivi Enfant")

def layout(**kwargs):
    return html.Div([
        dcc.Store(id="pp-session", storage_type="session"),
        dcc.Interval(id="pp-interval", interval=30000),  # refresh 30s

        # ── TOPBAR ────────────────────────────────────────────────────────
        html.Div([
            html.Div([
                html.Span("Nafa", style={"color":"var(--em)","fontFamily":"Instrument Serif,serif",
                    "fontSize":"22px","fontWeight":"400"}),
                html.Span(" Scolaire", style={"fontFamily":"Instrument Serif,serif",
                    "fontSize":"22px","fontStyle":"italic"}),
            ]),
            html.Div("Espace Parent", style={"fontFamily":"Instrument Serif,serif",
                "fontSize":"20px","fontWeight":"400","color":"var(--text-muted)"}),
            dcc.Link("Déconnexion →", href="/auth",
                     style={"fontSize":"10px","letterSpacing":"2px","color":"var(--muted)",
                            "textDecoration":"none","textTransform":"uppercase"}),
        ], className="topbar"),

        # ── ONGLETS ───────────────────────────────────────────────────────
        html.Div([
            html.Button("  Vue générale",    id="pp-tab-vue",    n_clicks=0, className="btn-sga btn-gold"),
            html.Button("  Bulletin",        id="pp-tab-bull",   n_clicks=0, className="btn-sga"),
            html.Button("  Absences",        id="pp-tab-abs",    n_clicks=0, className="btn-sga"),
            html.Button("  Emploi du temps", id="pp-tab-edt",    n_clicks=0, className="btn-sga"),
            html.Button("  Notifications",   id="pp-tab-notif",  n_clicks=0, className="btn-sga"),
        ], style={"display":"flex","gap":"8px","marginBottom":"20px","flexWrap":"wrap"}),

        html.Div(id="pp-panel-vue",   style={"display":"block"}),
        html.Div(id="pp-panel-bull",  style={"display":"none"}),
        html.Div(id="pp-panel-abs",   style={"display":"none"}),
        html.Div(id="pp-panel-edt",   style={"display":"none"}),
        html.Div(id="pp-panel-notif", style={"display":"none"}),

    ])


# ── Switcher onglets ──────────────────────────────────────────────────────────
@callback(
    Output("pp-panel-vue",   "style"),
    Output("pp-panel-bull",  "style"),
    Output("pp-panel-abs",   "style"),
    Output("pp-panel-edt",   "style"),
    Output("pp-panel-notif", "style"),
    Output("pp-tab-vue",     "className"),
    Output("pp-tab-bull",    "className"),
    Output("pp-tab-abs",     "className"),
    Output("pp-tab-edt",     "className"),
    Output("pp-tab-notif",   "className"),
    Input("pp-tab-vue",   "n_clicks"),
    Input("pp-tab-bull",  "n_clicks"),
    Input("pp-tab-abs",   "n_clicks"),
    Input("pp-tab-edt",   "n_clicks"),
    Input("pp-tab-notif", "n_clicks"),
)
def switch_tab(n1,n2,n3,n4,n5):
    from dash import ctx as _ctx
    show = {"display":"block"}
    hide = {"display":"none"}
    act  = "btn-sga btn-gold"
    nrm  = "btn-sga"
    tid  = _ctx.triggered_id
    if tid == "pp-tab-bull":  return hide,show,hide,hide,hide, nrm,act,nrm,nrm,nrm
    if tid == "pp-tab-abs":   return hide,hide,show,hide,hide, nrm,nrm,act,nrm,nrm
    if tid == "pp-tab-edt":   return hide,hide,hide,show,hide, nrm,nrm,nrm,act,nrm
    if tid == "pp-tab-notif": return hide,hide,hide,hide,show, nrm,nrm,nrm,nrm,act
    return show,hide,hide,hide,hide, act,nrm,nrm,nrm,nrm


# ── Chargement des panels ─────────────────────────────────────────────────────
def _get_student(session_data=None):
    """Retourne l'étudiant lié au compte parent connecté."""
    db = SessionLocal()
    try:
        # Si session disponible, chercher par linked_id
        if session_data and session_data.get("linked_id"):
            stu = db.get(Student, session_data["linked_id"])
            if stu:
                return stu
        # Fallback démo : premier étudiant
        return db.query(Student).filter_by(actif=True).first()
    finally:
        db.close()


@callback(Output("pp-panel-vue","children"),
          Input("pp-tab-vue","n_clicks"),
          Input("pp-interval","n_intervals"),
          State("pp-session","data"))
def render_vue(n, tick, session_data):
    db = SessionLocal()
    try:
        students = db.query(Student).filter_by(actif=True).all()
        if not students:
            return _empty("Aucun étudiant lié à ce compte parent.")

        stu = students[0]
        sid = stu.id
        grades   = db.query(Grade).filter_by(id_student=sid).all()
        att_all  = db.query(Attendance).filter_by(id_student=sid).all()
        sess_all = db.query(Sess).all()
        courses  = {c.code: c for c in db.query(Course).all()}
        classe   = db.query(Classe).get(stu.classe_id) if stu.classe_id else None

        tc   = sum(g.coefficient for g in grades)
        moy  = round(sum(g.note*g.coefficient for g in grades)/tc, 2) if tc else 0
        nb_abs = len(att_all)
        nb_sess= len(sess_all)
        taux = round(nb_abs/nb_sess*100, 1) if nb_sess else 0

        # Notifs non lues pour ce parent
        nb_notifs = db.query(Notification).filter(
            Notification.lu == False,
            Notification.student_id == sid,
        ).count()

        col_moy = "var(--red)" if moy < 10 else "var(--em)" if moy >= 12 else "var(--gold)"
        col_abs = "var(--red)" if taux > 20 else "var(--em)"

        # Alertes actives
        alertes = []
        if moy < 10:
            alertes.append(html.Div(
                f" Moyenne insuffisante : {moy:.2f}/20 — Contactez l'établissement.",
                className="sga-alert sga-alert-danger"))
        if taux > 20:
            alertes.append(html.Div(
                f" Taux d'absence élevé : {taux}% — Au-delà du seuil autorisé.",
                className="sga-alert sga-alert-warning"))
        if nb_notifs > 0:
            alertes.append(html.Div(
                f" {nb_notifs} nouvelle(s) notification(s) non lue(s).",
                className="sga-alert sga-alert-warning",
                style={"cursor":"pointer"}))
        if not alertes:
            alertes.append(html.Div("✓ Tout va bien — Aucune alerte.",
                className="sga-alert sga-alert-success"))

        # Graphe évolution notes
        notes_courbes = {}
        for g in grades:
            c = courses.get(g.course_code)
            lbl = c.libelle[:15] if c else g.course_code
            notes_courbes[lbl] = g.note

        fig_bar = go.Figure()
        if notes_courbes:
            couleurs = ["#0E6655" if v>=12 else "#D4720A" if v>=10 else "#B91C1C"
                        for v in notes_courbes.values()]
            fig_bar.add_trace(go.Bar(
                x=list(notes_courbes.keys()),
                y=list(notes_courbes.values()),
                marker_color=couleurs,
                text=[f"{v:.1f}" for v in notes_courbes.values()],
                textposition="outside",
            ))
            fig_bar.add_hline(y=10, line_dash="dash",
                              line_color="rgba(185,28,28,0.5)",
                              annotation_text="Seuil 10/20")
        fig_bar.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10,r=10,t=20,b=60),
            font=dict(family="Plus Jakarta Sans",size=11,color="#6B7280"),
            xaxis=dict(gridcolor="rgba(0,0,0,0.04)", tickangle=-30),
            yaxis=dict(range=[0,22], gridcolor="rgba(0,0,0,0.06)"),
            showlegend=False,
        )

        mention = ("Très Bien" if moy>=16 else "Bien" if moy>=14
                   else "Assez Bien" if moy>=12 else "Passable" if moy>=10 else "Insuffisant")

        return html.Div([
            *[html.Div(a, style={"marginBottom":"8px"}) for a in alertes],

            # KPIs
            html.Div([
                _kpi(f"{moy:.2f}/20", "Moyenne générale", col_moy),
                _kpi(mention,         "Mention",           "var(--em)"),
                _kpi(str(nb_abs),     "Absences",          col_abs),
                _kpi(f"{taux}%",      "Taux absence",      col_abs),
                _kpi(str(len(grades)),"Matières",          "var(--text-muted)"),
            ], style={"display":"grid","gridTemplateColumns":"repeat(5,1fr)",
                      "gap":"12px","marginBottom":"20px"}),

            # Fiche + graphe
            html.Div([
                # Fiche enfant
                html.Div([
                    html.Div("Fiche de votre enfant", className="sga-card-title",
                             style={"marginBottom":"20px"}),
                    html.Div([
                        html.Div(f"{stu.prenom[0]}{stu.nom[0]}", style={
                            "width":"60px","height":"60px","borderRadius":"50%",
                            "background":"linear-gradient(135deg,var(--em),var(--em-lt))",
                            "display":"flex","alignItems":"center","justifyContent":"center",
                            "fontSize":"22px","fontWeight":"700","color":"white","flexShrink":"0"}),
                        html.Div([
                            html.Div(f"{stu.prenom} {stu.nom}",
                                     style={"fontFamily":"Instrument Serif,serif",
                                            "fontSize":"22px","fontWeight":"400"}),
                            html.Div(stu.email, style={"color":"var(--muted)","fontSize":"12px"}),
                            html.Div(classe.nom if classe else "Classe non définie",
                                     style={"color":"var(--em)","fontSize":"12px",
                                            "fontWeight":"600","marginTop":"4px"}),
                        ]),
                    ], style={"display":"flex","gap":"16px","alignItems":"center",
                              "marginBottom":"20px"}),
                    *[_info_row(l, v, col) for l, v, col in [
                        ("Classe",     classe.nom if classe else "—", "var(--em)"),
                        ("Moyenne",    f"{moy:.2f} / 20", col_moy),
                        ("Mention",    mention, "var(--em)"),
                        ("Absences",   f"{nb_abs} / {nb_sess} séances", col_abs),
                        ("Matières évaluées", str(len(grades)), "var(--text-primary)"),
                    ]],
                ], className="sga-card", style={"flex":"0 0 320px"}),

                # Graphe notes
                html.Div([
                    html.Div("Notes par matière", className="sga-card-title",
                             style={"marginBottom":"12px"}),
                    dcc.Graph(figure=fig_bar, config={"displayModeBar":False},
                              style={"height":"320px"}),
                ], className="sga-card", style={"flex":"1"}),
            ], style={"display":"flex","gap":"16px","alignItems":"flex-start"}),
        ])
    finally:
        db.close()


@callback(Output("pp-panel-bull","children"),
          Input("pp-tab-bull","n_clicks"),
          State("pp-session","data"),
          prevent_initial_call=True)
def render_bulletin(n, session_data):
    db = SessionLocal()
    try:
        students = db.query(Student).filter_by(actif=True).all()
        if not students:
            return _empty("Aucun étudiant lié.")
        stu = students[0]
        sid = stu.id
        grades  = db.query(Grade).filter_by(id_student=sid).all()
        courses = {c.code: c for c in db.query(Course).all()}
        classe  = db.query(Classe).get(stu.classe_id) if stu.classe_id else None

        tc  = sum(g.coefficient for g in grades)
        moy = round(sum(g.note*g.coefficient for g in grades)/tc, 2) if tc else 0
        mention = ("Très Bien" if moy>=16 else "Bien" if moy>=14
                   else "Assez Bien" if moy>=12 else "Passable" if moy>=10 else "Insuffisant")
        col_moy = "var(--red)" if moy<10 else "var(--em)" if moy>=12 else "var(--gold)"

        rows = []
        for g in sorted(grades, key=lambda x: x.note, reverse=True):
            c   = courses.get(g.course_code)
            col = "var(--red)" if g.note<10 else "var(--em)" if g.note>=14 else "var(--text-primary)"
            mnt = ("TB" if g.note>=16 else "B" if g.note>=14
                   else "AB" if g.note>=12 else "P" if g.note>=10 else "F")
            cls_mnt = ("tag-green" if g.note>=14 else "tag-cyan" if g.note>=12
                       else "tag-orange" if g.note>=10 else "tag-red")
            rows.append(html.Tr([
                html.Td(c.libelle if c else g.course_code, style={"fontWeight":"600"}),
                html.Td(c.enseignant if c else "—",
                        style={"color":"var(--muted)","fontSize":"12px"}),
                html.Td(f"x{g.coefficient}", style={"textAlign":"center","color":"var(--muted)"}),
                html.Td(f"{g.note:.2f}/20",
                        style={"fontWeight":"700","color":col,"textAlign":"center",
                               "fontFamily":"monospace","fontSize":"14px"}),
                html.Td(html.Span(mnt, className=f"tag {cls_mnt}"),
                        style={"textAlign":"center"}),
                html.Td(_barre_note(g.note)),
            ]))

        return html.Div([
            # En-tête bulletin
            html.Div([
                html.Div([
                    html.Div(f"{stu.prenom} {stu.nom}",
                             style={"fontFamily":"Instrument Serif,serif","fontSize":"28px",
                                    "fontWeight":"400","marginBottom":"4px"}),
                    html.Div(classe.nom if classe else "—",
                             style={"color":"var(--em)","fontSize":"14px","fontWeight":"600"}),
                    html.Div(f"Année 2025–2026",
                             style={"color":"var(--muted)","fontSize":"12px"}),
                ]),
                html.Div([
                    html.Div(f"{moy:.2f}", style={"fontFamily":"Instrument Serif,serif",
                        "fontSize":"56px","fontWeight":"400","color":col_moy,"lineHeight":"1"}),
                    html.Div("/ 20", style={"fontSize":"18px","color":"var(--muted)","marginTop":"8px"}),
                    html.Div(mention, style={"fontSize":"13px","fontWeight":"700",
                        "color":col_moy,"marginTop":"4px","letterSpacing":"1px"}),
                ], style={"textAlign":"center"}),
            ], style={"display":"flex","justifyContent":"space-between","alignItems":"center",
                      "padding":"28px","background":"var(--em-xpale)",
                      "borderRadius":"10px 10px 0 0",
                      "borderBottom":"2px solid var(--em-pale)","marginBottom":"0"}),

            # Tableau des notes
            html.Div([
                html.Table([
                    html.Thead(html.Tr([
                        html.Th("Matière"), html.Th("Enseignant"),
                        html.Th("Coef."), html.Th("Note"), html.Th("Mention"),
                        html.Th("Progression"),
                    ])),
                    html.Tbody(rows),
                ], className="sga-table", style={"width":"100%"}),
            ], style={"padding":"0"}),

            # Pied de bulletin
            html.Div([
                html.Div([
                    html.Div("Appréciation générale", className="sga-label"),
                    html.Div(
                        _appreciation(moy),
                        style={"fontSize":"14px","color":"var(--text-primary)",
                               "lineHeight":"1.7","marginTop":"6px","fontStyle":"italic"}),
                ], style={"flex":"1"}),
                html.Div([
                    html.Div(f"Crédits validés", className="sga-label"),
                    html.Div(f"{sum(g.coefficient for g in grades if g.note>=10):.1f} / "
                             f"{sum(g.coefficient for g in grades):.1f}",
                             style={"fontFamily":"Instrument Serif,serif","fontSize":"28px",
                                    "color":"var(--em)","fontWeight":"400"}),
                ], style={"textAlign":"center"}),
            ], style={"display":"flex","gap":"32px","alignItems":"flex-start",
                      "padding":"20px 28px","background":"var(--bg-secondary)",
                      "borderRadius":"0 0 10px 10px","borderTop":"1px solid var(--border-lt)"}),
        ], className="sga-card", style={"padding":"0","overflow":"hidden"})
    finally:
        db.close()


@callback(Output("pp-panel-abs","children"),
          Input("pp-tab-abs","n_clicks"),
          State("pp-session","data"),
          prevent_initial_call=True)
def render_absences(n, session_data):
    db = SessionLocal()
    try:
        students = db.query(Student).filter_by(actif=True).all()
        if not students:
            return _empty("Aucun étudiant lié.")
        stu  = students[0]
        sid  = stu.id
        atts = db.query(Attendance).filter_by(id_student=sid).all()
        sess_map  = {s.id: s for s in db.query(Sess).all()}
        course_map= {c.code: c for c in db.query(Course).all()}

        # Grouper par cours
        par_cours = {}
        for a in atts:
            s = sess_map.get(a.id_session)
            if not s: continue
            if s.course_code not in par_cours:
                par_cours[s.course_code] = []
            par_cours[s.course_code].append(s.date)

        nb_sess_total = len(sess_map)
        nb_abs_total  = len(atts)
        taux_global   = round(nb_abs_total/nb_sess_total*100,1) if nb_sess_total else 0

        col_t = "var(--red)" if taux_global>20 else "var(--em)"

        rows = []
        for code, dates in sorted(par_cours.items(), key=lambda x: -len(x[1])):
            c = course_map.get(code)
            nb_s = len([s for s in sess_map.values() if s.course_code==code])
            nb_a = len(dates)
            taux = round(nb_a/nb_s*100,1) if nb_s else 0
            col  = "var(--red)" if taux>20 else "var(--text-primary)"
            rows.append(html.Tr([
                html.Td(c.libelle if c else code, style={"fontWeight":"600"}),
                html.Td(str(nb_a), style={"textAlign":"center","color":"var(--red)","fontWeight":"700"}),
                html.Td(str(nb_s), style={"textAlign":"center","color":"var(--muted)"}),
                html.Td(f"{taux}%", style={"textAlign":"center","color":col,"fontWeight":"700"}),
                html.Td(html.Span(
                    "⚠ Seuil dépassé" if taux>20 else "✓ OK",
                    style={"color":col,"fontSize":"11px","fontWeight":"600"})),
                html.Td([html.Div(d.strftime("%d/%m") if d else "—",
                                  style={"display":"inline-block","padding":"2px 6px",
                                         "background":"rgba(185,28,28,0.08)",
                                         "borderRadius":"4px","fontSize":"11px",
                                         "marginRight":"4px"})
                         for d in sorted(dates, reverse=True)[:5]]),
            ]))

        return html.Div([
            html.Div([
                _kpi(str(nb_abs_total),   "Absences totales",  "kpi-red"),
                _kpi(f"{taux_global}%",   "Taux global",       "kpi-orange"),
                _kpi(str(nb_sess_total),  "Séances au total",  "kpi-cyan"),
                _kpi(str(len(par_cours)), "Cours concernés",   "kpi-purple"),
            ], style={"display":"grid","gridTemplateColumns":"repeat(4,1fr)",
                      "gap":"12px","marginBottom":"20px"}),

            html.Div([
                html.Div("Historique des absences par matière", className="sga-card-title",
                         style={"marginBottom":"16px"}),
                html.Table([
                    html.Thead(html.Tr([html.Th(h) for h in
                        ["Matière","Absences","Séances","Taux","Statut","Dernières dates"]])),
                    html.Tbody(rows) if rows else html.Tbody([
                        html.Tr([html.Td("Aucune absence enregistrée",
                                         colSpan=6, style={"textAlign":"center",
                                         "color":"var(--em)","padding":"24px"})])
                    ]),
                ], className="sga-table", style={"width":"100%"}),
            ], className="sga-card"),
        ])
    finally:
        db.close()


@callback(Output("pp-panel-edt","children"),
          Input("pp-tab-edt","n_clicks"),
          State("pp-session","data"),
          prevent_initial_call=True)
def render_edt(n, session_data):
    db = SessionLocal()
    try:
        students = db.query(Student).filter_by(actif=True).all()
        if not students:
            return _empty("Aucun étudiant lié.")
        stu = students[0]
        classe_id = stu.classe_id

        # Récupérer l'emploi du temps de la classe
        try:
            edts = db.query(Creneau).filter_by(classe_id=classe_id).all()
        except Exception:
            edts = []

        # Cours de la classe (fallback ou grille)
        courses_classe = db.query(Course).all()

        if not edts:
            return html.Div([
                html.Div([
                    html.Div("Emploi du temps", className="sga-card-title",
                             style={"marginBottom":"8px"}),
                    html.Div("L'emploi du temps n'a pas encore été saisi. Voici les cours de la filière :",
                             style={"color":"var(--muted)","fontSize":"13px","marginBottom":"20px"}),
                    html.Div([
                        html.Div([
                            html.Div(cr.code, style={"fontWeight":"700","color":"var(--em)",
                                                      "fontSize":"12px","marginBottom":"4px"}),
                            html.Div(cr.libelle, style={"fontSize":"13px"}),
                            html.Div(cr.enseignant or "—",
                                     style={"fontSize":"11px","color":"var(--muted)","marginTop":"4px"}),
                        ], style={"padding":"12px 16px","background":"var(--em-xpale)",
                                  "borderRadius":"8px","border":"1px solid var(--em-pale)"})
                        for cr in courses_classe
                    ], style={"display":"grid","gridTemplateColumns":"repeat(3,1fr)","gap":"12px"}),
                ], className="sga-card"),
            ])

        # Grille : jour=int (0=Lun..5=Sam), heure_debut=float (8.0=08h00)
        HEURES = [8.0,9.0,10.0,11.0,12.0,13.0,14.0,15.0,16.0,17.0,18.0]
        JOURS_L = ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi"]

        grid = {j: {h: None for h in HEURES} for j in range(6)}
        for e in edts:
            j = e.jour if isinstance(e.jour, int) else 0
            h = float(e.heure_debut) if e.heure_debut else 8.0
            if j in grid and h in grid[j]:
                grid[j][h] = e

        def fmt_h(h): return f"{int(h):02d}h{int((h%1)*60):02d}"

        rows_edt = []
        for h in HEURES:
            cells = [html.Td(fmt_h(h), style={"fontSize":"11px","color":"var(--muted)",
                                               "fontWeight":"600","width":"70px","padding":"6px 8px",
                                               "whiteSpace":"nowrap"})]
            for j in range(6):
                entry = grid[j].get(h)
                if entry:
                    cells.append(html.Td(html.Div([
                        html.Div(entry.course_code, style={"fontSize":"11px","fontWeight":"700","color":"var(--em)"}),
                        html.Div(entry.salle or "", style={"fontSize":"10px","color":"var(--muted)"}),
                    ], style={"padding":"6px 8px","background":"var(--em-xpale)",
                              "borderRadius":"6px","border":"1px solid var(--em-pale)"}),
                    style={"padding":"4px"}))
                else:
                    cells.append(html.Td("", style={"padding":"4px","minWidth":"90px"}))
            rows_edt.append(html.Tr(cells))

        return html.Div([
            html.Div([
                html.Div("Emploi du temps de la semaine", className="sga-card-title",
                         style={"marginBottom":"16px"}),
                html.Div(style={"overflowX":"auto"}, children=[
                    html.Table([
                        html.Thead(html.Tr(
                            [html.Th("Heure")] +
                            [html.Th(j, style={"textAlign":"center","minWidth":"90px"})
                             for j in JOURS_L]
                        )),
                        html.Tbody(rows_edt),
                    ], className="sga-table", style={"width":"100%","minWidth":"700px"}),
                ]),
            ], className="sga-card"),
        ])
    finally:
        db.close()


@callback(Output("pp-panel-notif","children"),
          Input("pp-tab-notif","n_clicks"),
          Input("pp-interval","n_intervals"),
          State("pp-session","data"),
          prevent_initial_call=False)
def render_notifs(n, tick, session_data):
    from notif_service import get_notifs, marquer_lues
    db = SessionLocal()
    try:
        students = db.query(Student).filter_by(actif=True).all()
        sid = students[0].id if students else None
    finally:
        db.close()

    notifs = get_notifs("parent", student_id=sid, limit=50)

    # Marquer comme lues si on ouvre l'onglet
    if n and n > 0:
        ids_non_lus = [n_["id"] for n_ in notifs if not n_["lu"]]
        if ids_non_lus:
            marquer_lues(ids_non_lus)

    if not notifs:
        return html.Div([
            html.Div("", style={"fontSize":"48px","textAlign":"center","marginBottom":"12px"}),
            html.Div("Aucune notification", style={"textAlign":"center","color":"var(--muted)",
                     "fontSize":"16px","fontFamily":"Instrument Serif,serif"}),
        ], className="sga-card", style={"padding":"48px","textAlign":"center"})

    return html.Div([
        html.Div([
            html.Div(f"{len(notifs)} notification(s)", className="sga-card-title",
                     style={"marginBottom":"16px"}),
            html.Div([_carte_notif(n_) for n_ in notifs],
                     style={"display":"flex","flexDirection":"column","gap":"10px"}),
        ], className="sga-card"),
    ])


# ── HELPERS ───────────────────────────────────────────────────────────────────

def _empty(msg):
    return html.Div(msg, style={"color":"var(--muted)","padding":"40px","textAlign":"center"})

def _kpi(val, label, color):
    return html.Div([
        html.Div(val,   style={"fontFamily":"Instrument Serif,serif","fontSize":"28px",
                               "fontWeight":"400","color":color,"lineHeight":"1"}),
        html.Div(label, style={"fontSize":"11px","color":"var(--muted)","marginTop":"6px",
                               "letterSpacing":"0.5px"}),
    ], style={"background":"white","border":"1px solid var(--border-lt)",
              "borderRadius":"10px","padding":"16px 20px",
              "borderTop":f"3px solid {color}"})

def _info_row(label, val, color):
    return html.Div([
        html.Div(label, style={"fontSize":"11px","color":"var(--muted)","letterSpacing":"1px",
                               "textTransform":"uppercase"}),
        html.Div(val,   style={"fontFamily":"Instrument Serif,serif","fontSize":"18px",
                               "fontWeight":"400","color":color,"marginTop":"2px"}),
    ], style={"padding":"10px 0","borderBottom":"1px solid var(--border-lt)"})

def _barre_note(note):
    pct = min(note/20*100, 100)
    col = "#0E6655" if note>=12 else "#D4720A" if note>=10 else "#B91C1C"
    return html.Div(
        html.Div(style={"width":f"{pct}%","height":"100%","background":col,
                        "borderRadius":"3px","transition":"width 0.4s"}),
        style={"width":"100px","height":"8px","background":"var(--border-lt)",
               "borderRadius":"3px","overflow":"hidden"})

def _appreciation(moy):
    if moy >= 16:
        return "Excellents résultats. Félicitations pour ce travail remarquable et régulier."
    if moy >= 14:
        return "Bons résultats dans l'ensemble. Continuez sur cette lancée."
    if moy >= 12:
        return "Résultats satisfaisants. Des efforts supplémentaires permettront de progresser."
    if moy >= 10:
        return "Résultats passables. Des lacunes sont à combler rapidement pour assurer la réussite."
    return "Résultats insuffisants. Un accompagnement est fortement recommandé."

def _carte_notif(n):
    couleurs = {
        "danger":  ("rgba(185,28,28,0.06)",  "rgba(185,28,28,0.2)",  "var(--red)"),
        "warning": ("rgba(212,114,10,0.06)", "rgba(212,114,10,0.2)", "var(--gold)"),
        "success": ("rgba(14,102,85,0.06)",  "rgba(14,102,85,0.2)",  "var(--em)"),
        "info":    ("rgba(14,102,85,0.04)",  "rgba(14,102,85,0.1)",  "var(--em-lt)"),
    }
    bg, border, col = couleurs.get(n["type"], couleurs["info"])
    icones = {"absence":"","note":"","paiement":"","info":""}
    icone  = icones.get(n["categorie"], "")
    opacity = "1" if not n["lu"] else "0.6"

    return html.Div([
        html.Div([
            html.Span(icone, style={"fontSize":"20px","flexShrink":"0"}),
            html.Div([
                html.Div(n["titre"], style={"fontWeight":"700","fontSize":"14px",
                    "color":"var(--text-primary)","marginBottom":"4px"}),
                html.Div(n["message"], style={"fontSize":"13px","color":"var(--muted)",
                    "lineHeight":"1.6"}),
                html.Div(n["created_at"], style={"fontSize":"11px","color":"var(--muted)",
                    "marginTop":"6px"}),
            ], style={"flex":"1"}),
            html.Span("NON LUE" if not n["lu"] else "✓",
                style={"fontSize":"9px","letterSpacing":"1px","fontWeight":"700",
                       "color":col,"border":f"1px solid {border}",
                       "padding":"3px 8px","borderRadius":"20px","flexShrink":"0",
                       "background":bg}),
        ], style={"display":"flex","gap":"14px","alignItems":"flex-start"}),
    ], style={"padding":"16px 20px","borderRadius":"8px","border":f"1px solid {border}",
              "background":bg,"opacity":opacity,"transition":"opacity 0.3s"})
