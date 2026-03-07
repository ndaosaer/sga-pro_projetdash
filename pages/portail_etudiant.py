import dash
from dash import html, dcc, Input, Output, callback
from database import SessionLocal
from models import Student, Grade, Course, Session as Sess, Attendance
import plotly.graph_objects as go

dash.register_page(__name__, path="/portail-etudiant", name="Mon Espace")

T = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
         font=dict(family="JetBrains Mono", color="#8A8070", size=11),
         margin=dict(l=10,r=10,t=30,b=10))

def layout(**kwargs):
    return html.Div([
        dcc.Store(id="pe-trigger", data=1),
        # TOPBAR
        html.Div([
            html.Div([
                html.Span("SGA", style={"color":"var(--gold)","fontFamily":"Times New Roman,serif",
                    "fontSize":"20px","fontWeight":"700","letterSpacing":"4px"}),
                html.Span(" PRO", style={"fontFamily":"Times New Roman,serif",
                    "fontSize":"20px","fontStyle":"italic","letterSpacing":"2px"}),
            ]),
            html.Div("Mon Espace Étudiant", style={"fontFamily":"Times New Roman,serif",
                "fontSize":"22px","fontWeight":"700","color":"var(--text-primary)"}),
            html.Div([
                dcc.Link("← Déconnexion", href="/auth",
                         style={"fontSize":"10px","letterSpacing":"2px","color":"var(--muted)",
                                "textDecoration":"none","textTransform":"uppercase"}),
            ]),
        ], className="topbar"),

        html.Div(id="pe-content", style={"padding":"24px"}),
    ])


@callback(Output("pe-content","children"),
          Input("pe-trigger","data"))
def render(trigger):
    # On lit la session depuis le store — on passe par URL query en fallback
    # Ici on affiche le premier étudiant trouvé lié (dans un vrai système, depuis session-store)
    db = SessionLocal()
    try:
        students  = db.query(Student).filter_by(actif=True).all()
        courses   = db.query(Course).all()
        grades_all= db.query(Grade).all()
        sess_all  = db.query(Sess).all()
        att_all   = db.query(Attendance).all()
        course_map= {c.code: c for c in courses}

        if not students:
            return html.Div("Aucun étudiant trouvé.", style={"color":"var(--muted)","padding":"40px"})

        # Pour la démo : afficher le premier étudiant
        # En production : filtrer par session-store linked_id
        stu = students[0]
        sid = stu.id

        grades = [g for g in grades_all if g.id_student == sid]
        atts   = [a for a in att_all   if a.id_student == sid]

        # Calcul moyenne générale
        tc  = sum(g.coefficient for g in grades)
        moy = round(sum(g.note * g.coefficient for g in grades) / tc, 2) if tc else 0
        mention = ("Très Bien" if moy >= 16 else "Bien" if moy >= 14
                   else "Assez Bien" if moy >= 12 else "Passable" if moy >= 10 else "Insuffisant")
        nb_abs = len(atts)
        nb_sess= len(sess_all)
        taux_abs = round(nb_abs/nb_sess*100, 1) if nb_sess else 0

        col_moy = "var(--red)" if moy < 10 else "var(--green)" if moy >= 12 else "var(--copper)"
        col_abs = "var(--red)" if taux_abs > 20 else "var(--text-primary)"

        # KPIs
        kpis = html.Div([
            _kpi(f"{moy:.2f}/20", "Moyenne générale", col_moy),
            _kpi(mention,          "Mention",           "var(--gold)"),
            _kpi(str(nb_abs),      "Absences",          col_abs),
            _kpi(f"{taux_abs}%",  "Taux d'absence",    col_abs),
        ], style={"display":"grid","gridTemplateColumns":"repeat(4,1fr)","gap":"16px","marginBottom":"24px"})

        # Notes par matière
        rows = []
        for g in grades:
            c = course_map.get(g.course_code)
            col = "var(--red)" if g.note < 10 else "var(--green)" if g.note >= 14 else "var(--text-primary)"
            rows.append(html.Tr([
                html.Td(c.libelle if c else g.course_code, style={"fontWeight":"600"}),
                html.Td(c.enseignant if c else "—",
                        style={"color":"var(--muted)","fontSize":"12px"}),
                html.Td(f"{g.note:.2f}/20",
                        style={"fontWeight":"700","color":col,"textAlign":"center",
                               "fontFamily":"JetBrains Mono,monospace"}),
                html.Td(str(int(g.coefficient)),
                        style={"textAlign":"center","color":"var(--muted)"}),
            ]))

        table = html.Div([
            html.Div("Mes notes", className="sga-card-title",
                     style={"marginBottom":"16px"}),
            html.Table([
                html.Thead(html.Tr([
                    html.Th("Matière"), html.Th("Enseignant"),
                    html.Th("Note"), html.Th("Coef."),
                ])),
                html.Tbody(rows),
            ], className="sga-table", style={"width":"100%"}),
        ], className="sga-card", style={"marginBottom":"20px"})

        # Radar
        if grades:
            cats = [course_map[g.course_code].code if g.course_code in course_map else g.course_code
                    for g in grades]
            vals = [g.note for g in grades]
            fig = go.Figure(go.Scatterpolar(
                r=vals + [vals[0]], theta=cats + [cats[0]],
                fill="toself",
                fillcolor="rgba(184,146,42,0.12)",
                line=dict(color="var(--gold)", width=2),
                marker=dict(size=7, color="#B8922A"),
                name="Mes notes",
            ))
            fig.update_layout(**T, title="Profil académique",
                polar=dict(bgcolor="rgba(0,0,0,0)",
                    radialaxis=dict(visible=True, range=[0,20],
                        gridcolor="rgba(184,146,42,0.12)",
                        tickfont=dict(color="#8A8070", size=9)),
                    angularaxis=dict(gridcolor="rgba(184,146,42,0.1)",
                        tickfont=dict(color="#1E1A12", size=11))),
            )
            radar = html.Div([
                dcc.Graph(figure=fig, config={"displayModeBar":False}),
            ], className="sga-card")
        else:
            radar = html.Div()

        # Profil
        profil = html.Div([
            html.Div([
                html.Div(f"{stu.prenom[0]}{stu.nom[0]}",
                         style={"width":"64px","height":"64px","borderRadius":"50%",
                                "background":"var(--gold)","color":"var(--bg-primary)",
                                "display":"flex","alignItems":"center","justifyContent":"center",
                                "fontFamily":"Times New Roman,serif","fontSize":"24px",
                                "fontWeight":"700","marginBottom":"12px"}),
                html.Div(f"{stu.prenom} {stu.nom}",
                         style={"fontFamily":"Times New Roman,serif","fontSize":"22px",
                                "fontWeight":"700","marginBottom":"4px"}),
                html.Div(stu.email, style={"fontSize":"12px","color":"var(--muted)","marginBottom":"16px"}),
                html.Div(f"Né(e) le {stu.date_naissance.strftime('%d/%m/%Y') if stu.date_naissance else '—'}",
                         style={"fontSize":"12px","color":"var(--muted)"}),
            ], style={"textAlign":"center","padding":"8px 0","marginBottom":"20px",
                      "borderBottom":"1px solid var(--border)"}),
            html.Div("Mes matières", className="sga-card-title",
                     style={"marginBottom":"12px"}),
            *[html.Div([
                html.Div(style={"width":"8px","height":"8px","borderRadius":"50%","flexShrink":"0",
                                "background":course_map[g.course_code].couleur if g.course_code in course_map else "#B8922A"}),
                html.Div(course_map[g.course_code].libelle if g.course_code in course_map else g.course_code,
                         style={"fontSize":"13px"}),
            ], style={"display":"flex","gap":"10px","alignItems":"center","padding":"6px 0",
                      "borderBottom":"1px solid rgba(30,26,18,0.06)"})
              for g in grades],
        ], className="sga-card")

        return html.Div([
            kpis,
            html.Div([
                html.Div([profil], style={"width":"280px","flexShrink":"0"}),
                html.Div([table, radar], style={"flex":"1"}),
            ], style={"display":"flex","gap":"20px","alignItems":"flex-start"}),
        ])

    finally:
        db.close()


def _kpi(val, label, color="var(--text-primary)"):
    return html.Div([
        html.Div(val, className="kpi-value", style={"color":color,"fontSize":"32px"}),
        html.Div(label, className="kpi-label"),
    ], className="kpi-card")
