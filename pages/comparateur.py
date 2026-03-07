import dash
from dash import html, dcc, Input, Output, callback
import plotly.graph_objects as go
from database import SessionLocal
from models import Course, Student, Grade, Session, Attendance

dash.register_page(__name__, path="/comparateur", name="Comparateur")

T = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="JetBrains Mono", color="#8A8070", size=11),
    margin=dict(l=20, r=20, t=40, b=20),
    xaxis=dict(gridcolor="rgba(184,146,42,0.12)", linecolor="rgba(184,146,42,0.2)"),
    yaxis=dict(gridcolor="rgba(184,146,42,0.12)", linecolor="rgba(184,146,42,0.2)"),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#8A8070", size=11)),
)

def layout():
    db = SessionLocal()
    cours_opts = [{"label": f"{c.code} — {c.libelle}", "value": c.code}
                  for c in db.query(Course).all()]
    stu_opts   = [{"label": f"{s.nom} {s.prenom}", "value": s.id}
                  for s in db.query(Student).filter_by(actif=True).order_by(Student.nom).all()]
    db.close()

    return html.Div([
        html.Div([
            html.Div([
                html.Div("Comparateur", className="page-title"),
                html.Div("Analyse côte à côte — cours ou étudiants", className="page-subtitle"),
            ]),
        ], className="topbar"),

        # Sélecteur de mode
        html.Div([
            html.Div([
                html.Div("Mode de comparaison", className="sga-card-title",
                         style={"marginBottom":"16px"}),
                dcc.RadioItems(
                    id="comp-mode",
                    options=[
                        {"label": "  Comparer 2 cours",     "value": "cours"},
                        {"label": "  Comparer 2 étudiants", "value": "etudiants"},
                    ],
                    value="cours",
                    inline=True,
                    inputStyle={"marginRight":"6px"},
                    labelStyle={"marginRight":"28px","fontFamily":"JetBrains Mono,monospace",
                                "fontSize":"13px","cursor":"pointer","color":"var(--text-primary)"},
                ),
            ], className="sga-card", style={"marginBottom":"20px"}),
        ]),

        # Sélecteurs dynamiques
        html.Div(id="comp-selecteurs", style={"marginBottom":"20px"}),

        # Résultats
        html.Div(id="comp-resultats"),
    ])


@callback(
    Output("comp-selecteurs", "children"),
    Input("comp-mode", "value"),
)
def afficher_selecteurs(mode):
    db = SessionLocal()
    if mode == "cours":
        opts = [{"label": f"{c.code} — {c.libelle}", "value": c.code}
                for c in db.query(Course).all()]
        db.close()
        return html.Div([
            html.Div([
                html.Div([
                    html.Div("● Cours A", className="sga-card-title",
                             style={"marginBottom":"12px","color":"var(--gold)"}),
                    dcc.Dropdown(id="comp-a", options=opts,
                                 placeholder="Sélectionner le cours A…", clearable=False),
                ], className="sga-card", style={"flex":"1"}),
                html.Div("VS", style={
                    "fontFamily":"Times New Roman,serif","fontSize":"32px",
                    "fontWeight":"700","color":"var(--border)",
                    "display":"flex","alignItems":"center","padding":"0 8px",
                }),
                html.Div([
                    html.Div("● Cours B", className="sga-card-title",
                             style={"marginBottom":"12px","color":"var(--copper)"}),
                    dcc.Dropdown(id="comp-b", options=opts,
                                 placeholder="Sélectionner le cours B…", clearable=False),
                ], className="sga-card", style={"flex":"1"}),
            ], style={"display":"flex","gap":"16px","alignItems":"stretch"}),
        ])
    else:
        opts = [{"label": f"{s.nom} {s.prenom}", "value": s.id}
                for s in db.query(Student).filter_by(actif=True).order_by(Student.nom).all()]
        db.close()
        return html.Div([
            html.Div([
                html.Div([
                    html.Div("● Étudiant A", className="sga-card-title",
                             style={"marginBottom":"12px","color":"var(--gold)"}),
                    dcc.Dropdown(id="comp-a", options=opts,
                                 placeholder="Sélectionner l'étudiant A…", clearable=False),
                ], className="sga-card", style={"flex":"1"}),
                html.Div("VS", style={
                    "fontFamily":"Times New Roman,serif","fontSize":"32px",
                    "fontWeight":"700","color":"var(--border)",
                    "display":"flex","alignItems":"center","padding":"0 8px",
                }),
                html.Div([
                    html.Div("● Étudiant B", className="sga-card-title",
                             style={"marginBottom":"12px","color":"var(--copper)"}),
                    dcc.Dropdown(id="comp-b", options=opts,
                                 placeholder="Sélectionner l'étudiant B…", clearable=False),
                ], className="sga-card", style={"flex":"1"}),
            ], style={"display":"flex","gap":"16px","alignItems":"stretch"}),
        ])


@callback(
    Output("comp-resultats", "children"),
    Input("comp-a",    "value"),
    Input("comp-b",    "value"),
    Input("comp-mode", "value"),
)
def comparer(a, b, mode):
    if not a or not b:
        return html.Div("Sélectionnez les deux éléments à comparer.",
                        style={"color":"var(--muted)","textAlign":"center",
                               "padding":"60px","fontStyle":"italic","fontSize":"16px"})
    if a == b:
        return html.Div("Sélectionnez deux éléments différents.",
                        style={"color":"var(--copper)","textAlign":"center",
                               "padding":"40px","fontSize":"15px"})

    if mode == "cours":
        return _comparer_cours(a, b)
    else:
        return _comparer_etudiants(a, b)


# ── COMPARAISON COURS ─────────────────────────────────────────────────────────
def _comparer_cours(code_a, code_b):
    db = SessionLocal()
    ca = db.get(Course, code_a)
    cb = db.get(Course, code_b)
    grades   = db.query(Grade).all()
    sessions = db.query(Session).all()
    atts     = db.query(Attendance).all()
    students = db.query(Student).filter_by(actif=True).all()
    db.close()

    def stats_cours(code):
        g = [gr for gr in grades if gr.course_code == code]
        notes = [gr.note for gr in g]
        sess  = [s for s in sessions if s.course_code == code]
        heures = sum(s.duree for s in sess)
        sess_ids = {s.id for s in sess}
        nb_abs = sum(1 for a in atts if a.id_session in sess_ids)
        moy = round(sum(notes)/len(notes), 2) if notes else 0
        return {
            "notes": notes, "moy": moy,
            "min": min(notes) if notes else 0,
            "max": max(notes) if notes else 0,
            "heures": heures, "nb_sess": len(sess),
            "nb_abs": nb_abs, "nb_eval": len(g),
        }

    sa, sb = stats_cours(code_a), stats_cours(code_b)
    col_a, col_b = ca.couleur or "#B8922A", cb.couleur or "#9B5E2A"

    # ── KPIs côte à côte ──────────────────────────────────────────────────────
    kpis = html.Div([
        _kpi_vs("Moyenne", f"{sa['moy']:.2f}", f"{sb['moy']:.2f}", col_a, col_b),
        _kpi_vs("Note max", f"{sa['max']:.1f}", f"{sb['max']:.1f}", col_a, col_b),
        _kpi_vs("Note min", f"{sa['min']:.1f}", f"{sb['min']:.1f}", col_a, col_b),
        _kpi_vs("Heures", f"{sa['heures']}h", f"{sb['heures']}h", col_a, col_b),
        _kpi_vs("Séances", str(sa['nb_sess']), str(sb['nb_sess']), col_a, col_b),
        _kpi_vs("Absences", str(sa['nb_abs']), str(sb['nb_abs']), col_a, col_b),
    ], style={"display":"grid","gridTemplateColumns":"repeat(3,1fr)","gap":"16px",
              "marginBottom":"24px"})

    # ── Graphique barres groupées ─────────────────────────────────────────────
    fig_bar = go.Figure()
    metriques = ["Moyenne", "Note max", "Note min"]
    vals_a = [sa["moy"], sa["max"], sa["min"]]
    vals_b = [sb["moy"], sb["max"], sb["min"]]
    fig_bar.add_trace(go.Bar(name=code_a, x=metriques, y=vals_a,
        marker=dict(color=col_a, opacity=0.85),
        text=[f"{v:.1f}" for v in vals_a], textposition="outside",
        textfont=dict(size=11, color=col_a)))
    fig_bar.add_trace(go.Bar(name=code_b, x=metriques, y=vals_b,
        marker=dict(color=col_b, opacity=0.85),
        text=[f"{v:.1f}" for v in vals_b], textposition="outside",
        textfont=dict(size=11, color=col_b)))
    fig_bar.update_layout(**T, barmode="group", title="Comparaison des notes",
                          yaxis_range=[0, 22])

    # ── Distribution violon ───────────────────────────────────────────────────
    fig_vio = go.Figure()
    if sa["notes"]:
        fig_vio.add_trace(go.Violin(y=sa["notes"], name=code_a,
            fillcolor=f"rgba({_hr(col_a)},0.2)", line_color=col_a,
            box_visible=True, meanline_visible=True, points="all",
            marker=dict(size=5, color=col_a)))
    if sb["notes"]:
        fig_vio.add_trace(go.Violin(y=sb["notes"], name=code_b,
            fillcolor=f"rgba({_hr(col_b)},0.2)", line_color=col_b,
            box_visible=True, meanline_visible=True, points="all",
            marker=dict(size=5, color=col_b)))
    fig_vio.update_layout(**T, title="Distribution des notes", yaxis_range=[0,20])

    graphiques = html.Div([
        html.Div([dcc.Graph(figure=fig_bar, config={"displayModeBar":False})],
                 className="sga-card", style={"flex":"1"}),
        html.Div([dcc.Graph(figure=fig_vio, config={"displayModeBar":False})],
                 className="sga-card", style={"flex":"1"}),
    ], style={"display":"flex","gap":"20px"})

    # ── En-tête ───────────────────────────────────────────────────────────────
    entete = _entete_vs(
        ca.libelle, cb.libelle,
        f"{code_a} · {ca.enseignant or '—'}",
        f"{code_b} · {cb.enseignant or '—'}",
        col_a, col_b,
    )

    return html.Div([entete, kpis, graphiques])


# ── COMPARAISON ÉTUDIANTS ─────────────────────────────────────────────────────
def _comparer_etudiants(sid_a, sid_b):
    db = SessionLocal()
    from models import Student
    sa_obj = db.get(Student, sid_a)
    sb_obj = db.get(Student, sid_b)
    grades   = db.query(Grade).all()
    sessions = db.query(Session).all()
    atts     = db.query(Attendance).all()
    courses  = db.query(Course).all()
    db.close()

    col_a, col_b = "#B8922A", "#9B5E2A"

    def stats_stu(sid):
        g = [gr for gr in grades if gr.id_student == sid]
        tc  = sum(gr.coefficient for gr in g)
        moy = round(sum(gr.note*gr.coefficient for gr in g)/tc, 2) if tc else 0
        notes = [gr.note for gr in g]
        nb_abs = sum(1 for a in atts if a.id_student == sid)
        nb_sess = len(sessions)
        taux = round(nb_abs/nb_sess*100, 1) if nb_sess else 0
        par_cours = {}
        for gr in g:
            par_cours[gr.course_code] = gr.note
        return {
            "moy": moy, "notes": notes,
            "min": min(notes) if notes else 0,
            "max": max(notes) if notes else 0,
            "nb_abs": nb_abs, "taux_abs": taux,
            "nb_eval": len(g), "par_cours": par_cours,
        }

    sa, sb = stats_stu(sid_a), stats_stu(sid_b)
    nom_a = f"{sa_obj.prenom} {sa_obj.nom}"
    nom_b = f"{sb_obj.prenom} {sb_obj.nom}"

    # ── KPIs ──────────────────────────────────────────────────────────────────
    kpis = html.Div([
        _kpi_vs("Moyenne générale", f"{sa['moy']:.2f}", f"{sb['moy']:.2f}", col_a, col_b),
        _kpi_vs("Meilleure note",   f"{sa['max']:.1f}", f"{sb['max']:.1f}", col_a, col_b),
        _kpi_vs("Note la plus basse", f"{sa['min']:.1f}", f"{sb['min']:.1f}", col_a, col_b),
        _kpi_vs("Absences",  str(sa["nb_abs"]),   str(sb["nb_abs"]),   col_a, col_b),
        _kpi_vs("Taux abs.", f"{sa['taux_abs']}%", f"{sb['taux_abs']}%", col_a, col_b),
        _kpi_vs("Matières évaluées", str(sa["nb_eval"]), str(sb["nb_eval"]), col_a, col_b),
    ], style={"display":"grid","gridTemplateColumns":"repeat(3,1fr)","gap":"16px",
              "marginBottom":"24px"})

    # ── Radar par cours ───────────────────────────────────────────────────────
    cours_communs = [c for c in courses
                     if c.code in sa["par_cours"] and c.code in sb["par_cours"]]
    fig_radar = go.Figure()
    if cours_communs:
        cats = [c.code for c in cours_communs]
        fig_radar.add_trace(go.Scatterpolar(
            r=[sa["par_cours"][c.code] for c in cours_communs] + [sa["par_cours"][cours_communs[0].code]],
            theta=cats + [cats[0]], name=nom_a, fill="toself",
            fillcolor=f"rgba({_hr(col_a)},0.15)", line=dict(color=col_a, width=2),
            marker=dict(size=6, color=col_a)))
        fig_radar.add_trace(go.Scatterpolar(
            r=[sb["par_cours"][c.code] for c in cours_communs] + [sb["par_cours"][cours_communs[0].code]],
            theta=cats + [cats[0]], name=nom_b, fill="toself",
            fillcolor=f"rgba({_hr(col_b)},0.15)", line=dict(color=col_b, width=2),
            marker=dict(size=6, color=col_b)))
    fig_radar.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="JetBrains Mono", color="#8A8070", size=11),
        margin=dict(l=40, r=40, t=50, b=40),
        title="Profil académique comparé",
        polar=dict(bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0,20],
                            gridcolor="rgba(184,146,42,0.12)",
                            tickfont=dict(color="#8A8070", size=9)),
            angularaxis=dict(gridcolor="rgba(184,146,42,0.1)",
                             tickfont=dict(color="#1E1A12", size=11))),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#8A8070")),
    )

    # ── Barres par matière ────────────────────────────────────────────────────
    fig_bar = go.Figure()
    all_cours = list(set(list(sa["par_cours"].keys()) + list(sb["par_cours"].keys())))
    fig_bar.add_trace(go.Bar(
        name=nom_a,
        x=all_cours,
        y=[sa["par_cours"].get(c, 0) for c in all_cours],
        marker=dict(color=col_a, opacity=0.85),
        text=[f"{sa['par_cours'].get(c,0):.1f}" for c in all_cours],
        textposition="outside", textfont=dict(size=10, color=col_a),
    ))
    fig_bar.add_trace(go.Bar(
        name=nom_b,
        x=all_cours,
        y=[sb["par_cours"].get(c, 0) for c in all_cours],
        marker=dict(color=col_b, opacity=0.85),
        text=[f"{sb['par_cours'].get(c,0):.1f}" for c in all_cours],
        textposition="outside", textfont=dict(size=10, color=col_b),
    ))
    fig_bar.update_layout(**T, barmode="group", title="Notes par matière",
                          yaxis_range=[0, 22])

    graphiques = html.Div([
        html.Div([dcc.Graph(figure=fig_radar, config={"displayModeBar":False})],
                 className="sga-card", style={"flex":"1"}),
        html.Div([dcc.Graph(figure=fig_bar,   config={"displayModeBar":False})],
                 className="sga-card", style={"flex":"1"}),
    ], style={"display":"flex","gap":"20px"})

    entete = _entete_vs(nom_a, nom_b,
                        sa_obj.email or "—", sb_obj.email or "—",
                        col_a, col_b)
    return html.Div([entete, kpis, graphiques])


# ── HELPERS ───────────────────────────────────────────────────────────────────
def _hr(hx):
    hx = hx.lstrip("#")
    return f"{int(hx[0:2],16)},{int(hx[2:4],16)},{int(hx[4:6],16)}"

def _entete_vs(nom_a, nom_b, sub_a, sub_b, col_a, col_b):
    return html.Div([
        html.Div([
            html.Div(nom_a, style={"fontFamily":"Times New Roman,serif","fontSize":"22px",
                                    "fontWeight":"700","color":col_a,"marginBottom":"4px"}),
            html.Div(sub_a, style={"fontSize":"11px","color":"var(--muted)",
                                    "fontFamily":"JetBrains Mono,monospace"}),
        ], style={"flex":"1","textAlign":"left"}),
        html.Div("VS", style={"fontFamily":"Times New Roman,serif","fontSize":"40px",
                               "fontWeight":"700","color":"var(--border)",
                               "padding":"0 24px"}),
        html.Div([
            html.Div(nom_b, style={"fontFamily":"Times New Roman,serif","fontSize":"22px",
                                    "fontWeight":"700","color":col_b,"marginBottom":"4px"}),
            html.Div(sub_b, style={"fontSize":"11px","color":"var(--muted)",
                                    "fontFamily":"JetBrains Mono,monospace"}),
        ], style={"flex":"1","textAlign":"right"}),
    ], className="sga-card",
       style={"display":"flex","alignItems":"center","marginBottom":"20px",
              "borderTop":f"2px solid var(--border)"})

def _kpi_vs(label, val_a, val_b, col_a, col_b):
    try:
        n_a = float(val_a.replace("h","").replace("%",""))
        n_b = float(val_b.replace("h","").replace("%",""))
        win_a = n_a > n_b
        win_b = n_b > n_a
    except Exception:
        win_a = win_b = False

    return html.Div([
        html.Div(label, className="kpi-label", style={"marginBottom":"12px","textAlign":"center"}),
        html.Div([
            html.Div(val_a, style={
                "fontFamily":"Times New Roman,serif","fontSize":"28px","fontWeight":"700",
                "color":col_a, "flex":"1","textAlign":"center",
                "opacity":"1" if win_a or not win_b else "0.5",
            }),
            html.Div("·", style={"color":"var(--border)","fontSize":"20px","padding":"0 8px"}),
            html.Div(val_b, style={
                "fontFamily":"Times New Roman,serif","fontSize":"28px","fontWeight":"700",
                "color":col_b, "flex":"1","textAlign":"center",
                "opacity":"1" if win_b or not win_a else "0.5",
            }),
        ], style={"display":"flex","alignItems":"center"}),
    ], className="sga-card", style={"padding":"18px"})
