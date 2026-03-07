import dash
from dash import html, dcc, Input, Output, callback
from database import SessionLocal
from models import Student, Grade, Course, Session as Sess, Attendance

dash.register_page(__name__, path="/portail-parent", name="Suivi Enfant")

def layout(**kwargs):
    return html.Div([
        dcc.Store(id="pp-trigger", data=1),
        html.Div([
            html.Div([
                html.Span("SGA", style={"color":"var(--gold)","fontFamily":"Times New Roman,serif",
                    "fontSize":"20px","fontWeight":"700","letterSpacing":"4px"}),
                html.Span(" PRO", style={"fontFamily":"Times New Roman,serif",
                    "fontSize":"20px","fontStyle":"italic"}),
            ]),
            html.Div("Espace Parent", style={"fontFamily":"Times New Roman,serif",
                "fontSize":"22px","fontWeight":"700"}),
            dcc.Link("← Déconnexion", href="/auth",
                     style={"fontSize":"10px","letterSpacing":"2px","color":"var(--muted)",
                            "textDecoration":"none","textTransform":"uppercase"}),
        ], className="topbar"),
        html.Div(id="pp-content", style={"padding":"24px"}),
    ])


@callback(Output("pp-content","children"), Input("pp-trigger","data"))
def render(t):
    db = SessionLocal()
    try:
        students   = db.query(Student).filter_by(actif=True).all()
        courses    = db.query(Course).all()
        grades_all = db.query(Grade).all()
        sess_all   = db.query(Sess).all()
        att_all    = db.query(Attendance).all()
        course_map = {c.code: c for c in courses}

        if not students:
            return html.Div("Aucun étudiant lié à ce compte.",
                            style={"color":"var(--muted)","padding":"40px","textAlign":"center"})

        stu = students[0]  # En production : filtrer par session linked_id
        sid = stu.id

        grades = [g for g in grades_all if g.id_student == sid]
        atts   = [a for a in att_all   if a.id_student == sid]
        tc     = sum(g.coefficient for g in grades)
        moy    = round(sum(g.note*g.coefficient for g in grades)/tc, 2) if tc else 0
        nb_abs = len(atts)
        nb_sess= len(sess_all)
        taux   = round(nb_abs/nb_sess*100,1) if nb_sess else 0

        col_moy = "var(--red)" if moy < 10 else "var(--green)" if moy >= 12 else "var(--copper)"
        col_abs = "var(--red)" if taux > 20 else "var(--green)"

        # Alerte si problème
        alertes = []
        if moy < 10:
            alertes.append(html.Div(
                f" Moyenne insuffisante : {moy:.2f}/20 — Contactez l'établissement.",
                className="sga-alert sga-alert-danger", style={"marginBottom":"12px"}))
        if taux > 20:
            alertes.append(html.Div(
                f" Taux d'absence élevé : {taux}% — Au-delà du seuil autorisé de 20%.",
                className="sga-alert sga-alert-warning", style={"marginBottom":"12px"}))
        if not alertes:
            alertes.append(html.Div(
                " Tout va bien — Aucune alerte pour votre enfant.",
                className="sga-alert sga-alert-success", style={"marginBottom":"12px"}))

        # Fiche enfant
        fiche = html.Div([
            html.Div("Fiche de votre enfant", className="sga-card-title",
                     style={"marginBottom":"20px"}),
            html.Div([
                html.Div(f"{stu.prenom[0]}{stu.nom[0]}",
                         style={"width":"56px","height":"56px","borderRadius":"50%",
                                "background":"var(--gold)","color":"var(--bg-primary)",
                                "display":"flex","alignItems":"center","justifyContent":"center",
                                "fontFamily":"Times New Roman,serif","fontSize":"22px",
                                "fontWeight":"700","flexShrink":"0"}),
                html.Div([
                    html.Div(f"{stu.prenom} {stu.nom}",
                             style={"fontFamily":"Times New Roman,serif","fontSize":"20px","fontWeight":"700"}),
                    html.Div(stu.email, style={"color":"var(--muted)","fontSize":"12px"}),
                ]),
            ], style={"display":"flex","gap":"16px","alignItems":"center","marginBottom":"24px"}),

            html.Div([
                _info_row("Moyenne générale", f"{moy:.2f} / 20", col_moy),
                _info_row("Mention",
                          ("Très Bien" if moy >= 16 else "Bien" if moy >= 14
                           else "Assez Bien" if moy >= 12 else "Passable" if moy >= 10 else "Insuffisant"),
                          "var(--gold)"),
                _info_row("Absences", f"{nb_abs} absence(s) sur {nb_sess} séances", col_abs),
                _info_row("Taux d'absence", f"{taux}%", col_abs),
                _info_row("Matières évaluées", str(len(grades)), "var(--text-primary)"),
            ]),
        ], className="sga-card", style={"marginBottom":"20px"})

        # Tableau des notes
        rows = []
        for g in grades:
            c = course_map.get(g.course_code)
            col = "var(--red)" if g.note < 10 else "var(--green)" if g.note >= 14 else "var(--text-primary)"
            rows.append(html.Tr([
                html.Td(c.libelle if c else g.course_code),
                html.Td(c.enseignant if c else "—",
                        style={"color":"var(--muted)","fontSize":"12px"}),
                html.Td(f"{g.note:.2f}", style={"fontWeight":"700","color":col,
                         "textAlign":"center","fontFamily":"JetBrains Mono,monospace"}),
            ]))

        notes_table = html.Div([
            html.Div("Résultats par matière", className="sga-card-title",
                     style={"marginBottom":"16px"}),
            html.Table([
                html.Thead(html.Tr([html.Th("Matière"),html.Th("Enseignant"),html.Th("Note /20")])),
                html.Tbody(rows),
            ], className="sga-table", style={"width":"100%"}),
        ], className="sga-card")

        return html.Div([
            *alertes,
            html.Div([
                html.Div([fiche], style={"width":"360px","flexShrink":"0"}),
                html.Div([notes_table], style={"flex":"1"}),
            ], style={"display":"flex","gap":"20px","alignItems":"flex-start"}),
        ])
    finally:
        db.close()


def _info_row(label, val, color):
    return html.Div([
        html.Div(label, style={"fontSize":"12px","color":"var(--muted)","letterSpacing":"1px"}),
        html.Div(val,   style={"fontFamily":"Times New Roman,serif","fontSize":"18px",
                               "fontWeight":"700","color":color}),
    ], style={"padding":"10px 0","borderBottom":"1px solid var(--border)"})
