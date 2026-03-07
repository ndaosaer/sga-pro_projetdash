import dash
from dash import html, dcc, Input, Output, callback
from database import SessionLocal
from models import Student, Course, Session as Sess, Attendance
from datetime import date

dash.register_page(__name__, path="/portail-secretaire", name="Secrétariat")

def layout(**kwargs):
    return html.Div([
        dcc.Store(id="ps-trigger", data=1),
        html.Div([
            html.Div([
                html.Span("SGA", style={"color":"var(--gold)","fontFamily":"Times New Roman,serif",
                    "fontSize":"20px","fontWeight":"700","letterSpacing":"4px"}),
                html.Span(" PRO", style={"fontFamily":"Times New Roman,serif",
                    "fontSize":"20px","fontStyle":"italic"}),
            ]),
            html.Div("Espace Secrétariat", style={"fontFamily":"Times New Roman,serif",
                "fontSize":"22px","fontWeight":"700"}),
            dcc.Link("Déconnexion", href="/auth",
                     style={"fontSize":"10px","letterSpacing":"2px","color":"var(--muted)",
                            "textDecoration":"none","textTransform":"uppercase"}),
        ], className="topbar"),

        html.Div([
            html.Button("Étudiants",  id="ps-tab-stu", n_clicks=0, className="btn-sga btn-gold"),
            html.Button("Cours",      id="ps-tab-crs", n_clicks=0, className="btn-sga"),
            html.Button("Présences",  id="ps-tab-att", n_clicks=0, className="btn-sga"),
            html.Button("Calendrier", id="ps-tab-cal", n_clicks=0, className="btn-sga"),
        ], style={"display":"flex","gap":"8px","padding":"16px 24px",
                  "borderBottom":"1px solid var(--border)","background":"var(--bg-card)"}),

        html.Div(id="ps-content", style={"padding":"24px"}),
    ])


@callback(
    Output("ps-content","children"),
    Input("ps-tab-stu","n_clicks"),
    Input("ps-tab-crs","n_clicks"),
    Input("ps-tab-att","n_clicks"),
    Input("ps-tab-cal","n_clicks"),
    Input("ps-trigger","data"),
)
def render_tab(n_stu, n_crs, n_att, n_cal, trigger):
    ctx = dash.callback_context
    tab = "stu"
    if ctx.triggered:
        tid = ctx.triggered[0]["prop_id"].split(".")[0]
        if "crs" in tid: tab = "crs"
        elif "att" in tid: tab = "att"
        elif "cal" in tid: tab = "cal"

    db = SessionLocal()
    try:
        if tab == "stu":
            students = db.query(Student).order_by(Student.nom).all()
            rows = [html.Tr([
                html.Td(f"{s.nom} {s.prenom}", style={"fontWeight":"600"}),
                html.Td(s.email, style={"color":"var(--muted)","fontSize":"12px"}),
                html.Td(s.date_naissance.strftime("%d/%m/%Y") if s.date_naissance else "—",
                        style={"color":"var(--muted)","fontSize":"12px"}),
                html.Td(html.Span("Actif" if s.actif else "Inactif",
                        style={"color":"var(--green)" if s.actif else "var(--red)",
                               "fontWeight":"600","fontSize":"11px"})),
            ]) for s in students]
            return html.Div([
                html.Div([
                    html.Div(f"{len(students)} étudiants inscrits",
                             className="sga-card-title", style={"marginBottom":"16px"}),
                    html.Table([
                        html.Thead(html.Tr([
                            html.Th("Nom & Prénom"), html.Th("Email"),
                            html.Th("Date naissance"), html.Th("Statut"),
                        ])),
                        html.Tbody(rows),
                    ], className="sga-table", style={"width":"100%"}),
                ], className="sga-card"),
            ])

        elif tab == "crs":
            courses = db.query(Course).all()
            rows = [html.Tr([
                html.Td(c.code, style={"fontFamily":"JetBrains Mono,monospace","fontWeight":"600",
                                        "color":c.couleur or "var(--gold)"}),
                html.Td(c.libelle),
                html.Td(c.enseignant or "—", style={"color":"var(--muted)"}),
                html.Td(f"{c.volume_horaire}h", style={"fontFamily":"JetBrains Mono,monospace"}),
            ]) for c in courses]
            return html.Div([
                html.Div([
                    html.Div(f"{len(courses)} cours au programme",
                             className="sga-card-title", style={"marginBottom":"16px"}),
                    html.Table([
                        html.Thead(html.Tr([
                            html.Th("Code"), html.Th("Matière"),
                            html.Th("Enseignant"), html.Th("Volume"),
                        ])),
                        html.Tbody(rows),
                    ], className="sga-table", style={"width":"100%"}),
                ], className="sga-card"),
            ])

        elif tab == "att":
            sessions  = db.query(Sess).order_by(Sess.date.desc()).limit(30).all()
            atts      = db.query(Attendance).all()
            courses   = {c.code: c for c in db.query(Course).all()}
            att_count = {}
            for a in atts:
                att_count[a.id_session] = att_count.get(a.id_session, 0) + 1
            rows = [html.Tr([
                html.Td(s.date.strftime("%d/%m/%Y"),
                        style={"fontFamily":"JetBrains Mono,monospace"}),
                html.Td(s.course_code, style={"color":"var(--gold)","fontWeight":"600",
                         "fontFamily":"JetBrains Mono,monospace"}),
                html.Td(courses[s.course_code].libelle if s.course_code in courses else "—"),
                html.Td(f"{s.duree}h"),
                html.Td(str(att_count.get(s.id, 0)),
                        style={"color":"var(--red)" if att_count.get(s.id,0) > 0 else "var(--green)",
                               "fontWeight":"600"}),
            ]) for s in sessions]
            return html.Div([
                html.Div([
                    html.Div("30 dernières séances", className="sga-card-title",
                             style={"marginBottom":"16px"}),
                    html.Table([
                        html.Thead(html.Tr([
                            html.Th("Date"), html.Th("Code"),
                            html.Th("Matière"), html.Th("Durée"), html.Th("Absences"),
                        ])),
                        html.Tbody(rows),
                    ], className="sga-table", style={"width":"100%"}),
                ], className="sga-card"),
            ])

        else:  # cal
            today    = date.today()
            sessions = db.query(Sess).filter(Sess.date >= today).order_by(Sess.date).limit(20).all()
            courses  = {c.code: c for c in db.query(Course).all()}

            if sessions:
                items = []
                for s in sessions:
                    col = courses[s.course_code].couleur if s.course_code in courses else "var(--gold)"
                    lib = courses[s.course_code].libelle if s.course_code in courses else "—"
                    items.append(html.Div([
                        html.Div(style={"width":"4px","background":col,
                                        "borderRadius":"2px","flexShrink":"0"}),
                        html.Div([
                            html.Div(s.date.strftime("%A %d %B").capitalize(),
                                     style={"fontWeight":"700","fontSize":"14px"}),
                            html.Div(f"{s.course_code} — {lib}",
                                     style={"color":"var(--muted)","fontSize":"12px"}),
                            html.Div(s.theme or "—",
                                     style={"color":"var(--gold)","fontSize":"12px"}),
                        ]),
                        html.Div(f"{s.duree}h",
                                 style={"fontFamily":"JetBrains Mono,monospace",
                                        "color":"var(--gold)","fontWeight":"700",
                                        "marginLeft":"auto"}),
                    ], style={"display":"flex","gap":"12px","alignItems":"center",
                              "padding":"14px","background":"var(--bg-secondary)",
                              "borderRadius":"4px","marginBottom":"8px"}))
            else:
                items = [html.Div("Aucune séance planifiée.",
                                  style={"color":"var(--muted)","textAlign":"center","padding":"40px"})]

            return html.Div([
                html.Div([
                    html.Div("Prochaines séances planifiées", className="sga-card-title",
                             style={"marginBottom":"16px"}),
                    *items,
                ], className="sga-card"),
            ])

    finally:
        db.close()
