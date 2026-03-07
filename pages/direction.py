import dash
from dash import html, dcc, Input, Output, callback
import plotly.graph_objects as go
from database import SessionLocal
from models import Student, Course, Session, Grade, Attendance, Notification, FraisScolarite, Paiement, Candidat, Concours
from datetime import date, datetime, timedelta
from sqlalchemy import func

dash.register_page(__name__, path="/direction", name="Direction")

T = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="JetBrains Mono", color="#8A8070", size=11),
    margin=dict(l=10, r=10, t=36, b=10),
    xaxis=dict(gridcolor="rgba(184,146,42,0.08)", linecolor="rgba(184,146,42,0.15)",
               tickfont=dict(color="#8A8070", size=10)),
    yaxis=dict(gridcolor="rgba(184,146,42,0.08)", linecolor="rgba(184,146,42,0.15)",
               tickfont=dict(color="#8A8070", size=10)),
)
GOLD   = "#B8922A"
GREEN  = "#2D6A3F"
RED    = "#8B2500"
COPPER = "#8B5E3C"
ANNEE  = "2025-2026"


def layout():
    return html.Div([
        dcc.Interval(id="dir-interval", interval=120_000, n_intervals=0, disabled=False),
        dcc.Store(id="dir-loaded", data=False),

        html.Div([
            html.Div([
                html.Div("Tableau de bord Direction", className="page-title"),
                html.Div(f"Vision consolidee — {date.today().strftime('%A %d %B %Y').capitalize()}",
                         className="page-subtitle"),
            ]),
            html.Div(id="dir-last-update",
                     style={"fontSize":"11px","color":"var(--muted)","letterSpacing":"1px"}),
        ], className="topbar"),

        html.Div([
            html.Div(id="dir-content", style={"padding":"24px"}),
            html.Div(id="dir-skeleton", children=[
                html.Div(style={"height":"80px","background":"var(--bg-card)",
                         "borderRadius":"6px","marginBottom":"16px",
                         "animation":"pulse 1.5s infinite",
                         "border":"1px solid var(--border)"}),
                html.Div([
                    html.Div(style={"height":"260px","background":"var(--bg-card)",
                             "borderRadius":"6px","flex":"2",
                             "border":"1px solid var(--border)"}),
                    html.Div(style={"height":"260px","background":"var(--bg-card)",
                             "borderRadius":"6px","flex":"1",
                             "border":"1px solid var(--border)"}),
                ], style={"display":"flex","gap":"20px","marginBottom":"16px",
                          "padding":"0 24px"}),
            ], style={"padding":"24px"}),
        ]),
    ])


@callback(
    Output("dir-content",      "children"),
    Output("dir-last-update",  "children"),
    Output("dir-skeleton",     "style"),
    Input("dir-interval",      "n_intervals"),
)
def render(n):
    db = SessionLocal()
    try:
        data = _collect_data(db)
    finally:
        db.close()

    last = f"Mis a jour a {datetime.now().strftime('%H:%M:%S')}"
    return _build_layout(data), last, {"display":"none","padding":"24px"}


# ═══════════════════════════════════════════════
# COLLECTE DES DONNEES
# ═══════════════════════════════════════════════
def _collect_data(db):
    d = {}

    # Academique
    students      = db.query(Student).filter_by(actif=True).all()
    courses       = db.query(Course).all()
    sessions      = db.query(Session).all()
    grades        = db.query(Grade).all()
    attendances   = db.query(Attendance).all()
    notifs        = db.query(Notification).all()

    d["nb_students"]  = len(students)
    d["nb_courses"]   = len(courses)
    d["nb_sessions"]  = len(sessions)
    notes = [g.note for g in grades]
    d["avg_global"]   = round(sum(notes) / len(notes), 2) if notes else 0
    d["nb_grades"]    = len(grades)

    # Taux d'absence global
    d["nb_absences"]  = len(attendances)
    d["taux_abs"]     = round(len(attendances) / len(sessions) / max(1, len(students)) * 100, 1) if sessions else 0

    # Alertes non lues
    d["nb_alertes"]   = db.query(Notification).filter_by(lu=False).count()
    d["alertes"]      = db.query(Notification).filter_by(lu=False)\
                          .order_by(Notification.created_at.desc()).limit(5).all()

    # Mentions
    mentions = {"Tres Bien":0, "Bien":0, "Assez Bien":0, "Passable":0, "Insuffisant":0}
    moyennes_etu = []
    for s in students:
        gs = [g for g in grades if g.id_student == s.id]
        if not gs:
            continue
        tc  = sum(g.coefficient for g in gs)
        moy = sum(g.note * g.coefficient for g in gs) / tc if tc else 0
        moyennes_etu.append((s, moy))
        if moy >= 16:   mentions["Tres Bien"]   += 1
        elif moy >= 14: mentions["Bien"]         += 1
        elif moy >= 12: mentions["Assez Bien"]   += 1
        elif moy >= 10: mentions["Passable"]      += 1
        else:           mentions["Insuffisant"]   += 1
    d["mentions"]      = mentions
    d["moyennes_etu"]  = sorted(moyennes_etu, key=lambda x: x[1])
    d["top5"]          = sorted(moyennes_etu, key=lambda x: x[1], reverse=True)[:5]
    d["bottom5"]       = sorted(moyennes_etu, key=lambda x: x[1])[:5]

    # Moyennes par cours
    moy_cours = []
    for c in courses:
        gs = [g for g in grades if g.course_code == c.code]
        if gs:
            tc  = sum(g.coefficient for g in gs)
            moy = sum(g.note * g.coefficient for g in gs) / tc if tc else 0
            moy_cours.append((c.code, c.libelle, round(moy, 2), c.couleur or GOLD))
    d["moy_cours"] = sorted(moy_cours, key=lambda x: x[2], reverse=True)

    # Seances par mois (6 derniers mois)
    six_mois = date.today() - timedelta(days=180)
    mois_counts = {}
    for s in sessions:
        if s.date and s.date >= six_mois:
            key = s.date.strftime("%b %Y")
            mois_counts[key] = mois_counts.get(key, 0) + 1
    d["seances_mois"] = mois_counts

    # Financier
    try:
        frais_all = db.query(FraisScolarite).filter_by(annee=ANNEE).all()
        pays_all  = db.query(Paiement).filter_by(valide=True).all()
        total_du   = sum(f.montant_total for f in frais_all)
        total_paye = sum(p.montant for p in pays_all)
        total_reste = max(0, total_du - total_paye)
        taux_rec   = round(total_paye / total_du * 100, 1) if total_du else 0
        nb_a_jour  = 0
        nb_retard  = 0
        for f in frais_all:
            paye = sum(p.montant for p in pays_all if p.student_id == f.student_id)
            if paye >= f.montant_total:
                nb_a_jour += 1
            else:
                nb_retard += 1
        d["financier"] = {
            "total_du":    total_du,
            "total_paye":  total_paye,
            "total_reste": total_reste,
            "taux_rec":    taux_rec,
            "nb_a_jour":   nb_a_jour,
            "nb_retard":   nb_retard,
            "nb_frais":    len(frais_all),
        }
    except Exception:
        d["financier"] = None

    # Concours
    try:
        concours = db.query(Concours).filter_by(actif=True).order_by(Concours.annee.desc()).first()
        if concours:
            candidats = db.query(Candidat).filter_by(concours_id=concours.id).all()
            d["concours"] = {
                "nom":      concours.nom,
                "annee":    concours.annee,
                "total":    len(candidats),
                "admis":    sum(1 for c in candidats if c.admis),
                "valides":  sum(1 for c in candidats if c.statut == "valide"),
                "payes":    sum(1 for c in candidats if c.paiement_statut in ("paye","simule")),
            }
        else:
            d["concours"] = None
    except Exception:
        d["concours"] = None

    return d


# ═══════════════════════════════════════════════
# CONSTRUCTION DU LAYOUT
# ═══════════════════════════════════════════════
def student_row(s, moy, rank=None):
    col = GREEN if moy >= 12 else COPPER if moy >= 10 else RED
    return html.Div([
        html.Div(str(rank) if rank else "", style={"width":"24px","fontSize":"11px",
                 "color":"var(--muted)","fontFamily":"JetBrains Mono,monospace",
                 "flexShrink":"0"}),
        html.Div(f"{s.prenom} {s.nom}", style={"flex":"1","fontSize":"13px","fontWeight":"600"}),
        html.Div(f"{moy:.2f}/20", style={"fontFamily":"JetBrains Mono,monospace",
                 "fontWeight":"700","color":col,"fontSize":"13px"}),
    ], style={"display":"flex","alignItems":"center","gap":"12px","padding":"8px 0",
              "borderBottom":"1px solid var(--border)"})


def _build_layout(d):
    fin = d.get("financier")
    con = d.get("concours")

    # ── Ligne 1 : KPIs globaux ──
    kpi_row1 = html.Div([
        _kpi(str(d["nb_students"]),      "Etudiants actifs",      GOLD),
        _kpi(str(d["nb_courses"]),       "Cours au programme",    "var(--muted)"),
        _kpi(str(d["nb_sessions"]),      "Seances enregistrees",  "var(--muted)"),
        _kpi(f"{d['avg_global']:.2f}/20","Moyenne promotion",     GREEN if d["avg_global"] >= 12 else RED),
        _kpi(f"{d['taux_abs']}%",        "Taux absence moyen",    RED if d["taux_abs"] > 15 else GREEN),
        _kpi(str(d["nb_alertes"]),       "Alertes actives",       RED if d["nb_alertes"] > 0 else GREEN),
    ], style={"display":"grid","gridTemplateColumns":"repeat(6,1fr)","gap":"16px","marginBottom":"24px"})

    # ── Ligne 2 : Financier ──
    if fin:
        kpi_fin = html.Div([
            _kpi(f"{fin['total_du']:,.0f}",   "Total du (FCFA)",        "var(--text-primary)"),
            _kpi(f"{fin['total_paye']:,.0f}",  "Encaisse (FCFA)",        GREEN),
            _kpi(f"{fin['total_reste']:,.0f}", "Reste a percevoir",      RED if fin["total_reste"] > 0 else GREEN),
            _kpi(f"{fin['taux_rec']}%",        "Taux de recouvrement",   GREEN if fin["taux_rec"] >= 70 else COPPER),
            _kpi(str(fin["nb_a_jour"]),        "Etudiants a jour",       GREEN),
            _kpi(str(fin["nb_retard"]),        "Etudiants en retard",    RED if fin["nb_retard"] > 0 else GREEN),
        ], style={"display":"grid","gridTemplateColumns":"repeat(6,1fr)","gap":"16px","marginBottom":"24px"})
        fin_section = html.Div([
            html.Div("Situation financiere", style={"fontSize":"10px","letterSpacing":"3px",
                     "textTransform":"uppercase","color":"var(--muted)","marginBottom":"12px"}),
            kpi_fin,
            # Jauge recouvrement
            html.Div([
                html.Div([
                    html.Span("Recouvrement scolarite ", style={"fontSize":"13px","fontWeight":"600"}),
                    html.Span(f"{fin['annee'] if 'annee' in fin else ANNEE}",
                              style={"fontSize":"11px","color":"var(--muted)"}),
                ], style={"marginBottom":"8px"}),
                html.Div(style={"height":"14px","borderRadius":"7px","background":"var(--border)","overflow":"hidden"},
                         children=[html.Div(style={
                             "height":"100%","borderRadius":"7px","transition":"width 1s",
                             "width":f"{fin['taux_rec']}%",
                             "background":f"linear-gradient(90deg, {GREEN}, {GOLD})",
                         })]),
                html.Div([
                    html.Span(f"{fin['taux_rec']}% encaisse",
                              style={"fontSize":"11px","color":"var(--muted)"}),
                    html.Span(f"{fin['nb_a_jour']} etudiants a jour sur {fin['nb_frais']}",
                              style={"fontSize":"11px","color":"var(--muted)"}),
                ], style={"display":"flex","justifyContent":"space-between","marginTop":"6px"}),
            ], style={"padding":"16px","background":"var(--bg-secondary)","borderRadius":"4px"}),
        ], style={"marginBottom":"24px","padding":"20px","background":"var(--bg-card)",
                  "border":"1px solid var(--border)","borderRadius":"6px"})
    else:
        fin_section = html.Div(
            "Module paiements non configure.",
            style={"color":"var(--muted)","fontSize":"13px","marginBottom":"24px",
                   "padding":"16px","background":"var(--bg-card)","borderRadius":"6px",
                   "border":"1px solid var(--border)"})

    # ── Graphiques ──
    # Moyennes par cours
    if d["moy_cours"]:
        codes  = [x[0] for x in d["moy_cours"]]
        moys   = [x[2] for x in d["moy_cours"]]
        colors = [GREEN if m >= 12 else COPPER if m >= 10 else RED for m in moys]
        fig_cours = go.Figure(go.Bar(
            x=codes, y=moys, marker_color=colors, marker_line_width=0,
            text=[f"{m:.1f}" for m in moys], textposition="outside",
            textfont=dict(size=10, color="#8A8070"),
        ))
        T2 = {k:v for k,v in T.items() if k != "yaxis"}
        fig_cours.update_layout(**T2, title="Moyennes par cours",
                                title_font=dict(size=13, color="#1E1A12"),
                                yaxis=dict(**T["yaxis"], range=[0, 21]))
    else:
        fig_cours = go.Figure()
        fig_cours.update_layout(**T)

    # Repartition des mentions
    mentions = d["mentions"]
    fig_mentions = go.Figure(go.Pie(
        labels=list(mentions.keys()),
        values=list(mentions.values()),
        hole=0.55,
        marker=dict(colors=[GREEN, "#4A9A60", COPPER, "#C49A3C", RED]),
        textfont=dict(size=10),
        showlegend=True,
    ))
    T2 = {k:v for k,v in T.items() if k not in ("yaxis","xaxis")}
    fig_mentions.update_layout(**T2, title="Repartition des mentions",
                               title_font=dict(size=13, color="#1E1A12"),
                               legend=dict(font=dict(size=9, color="#8A8070"),
                                           orientation="v", x=1, y=0.5))

    # Seances par mois
    if d["seances_mois"]:
        mois_keys = list(d["seances_mois"].keys())
        mois_vals = list(d["seances_mois"].values())
        fig_mois = go.Figure(go.Scatter(
            x=mois_keys, y=mois_vals, mode="lines+markers",
            line=dict(color=GOLD, width=2),
            marker=dict(size=7, color=GOLD),
            fill="tozeroy", fillcolor="rgba(184,146,42,0.08)",
        ))
        fig_mois.update_layout(**T, title="Activite pedagogique (6 mois)",
                               title_font=dict(size=13, color="#1E1A12"))
    else:
        fig_mois = go.Figure()
        fig_mois.update_layout(**T)

    graphiques = html.Div([
        html.Div([
            dcc.Graph(figure=fig_cours, config={"displayModeBar":False}, style={"height":"260px"}),
        ], className="sga-card", style={"flex":"2"}),
        html.Div([
            dcc.Graph(figure=fig_mentions, config={"displayModeBar":False}, style={"height":"260px"}),
        ], className="sga-card", style={"flex":"1"}),
    ], style={"display":"flex","gap":"20px","marginBottom":"20px"})

    graphique_mois = html.Div([
        dcc.Graph(figure=fig_mois, config={"displayModeBar":False}, style={"height":"200px"}),
    ], className="sga-card", style={"marginBottom":"20px"})

    # ── Top 5 / Bottom 5 ──
    classement = html.Div([
        html.Div([
            html.Div("Top 5 etudiants", className="sga-card-title", style={"marginBottom":"12px"}),
            *(_top5_rows(d["top5"])),
        ], className="sga-card", style={"flex":"1"}),
        html.Div([
            html.Div("Etudiants en difficulte", className="sga-card-title", style={"marginBottom":"12px"}),
            *(_bottom5_rows(d["bottom5"])),
        ], className="sga-card", style={"flex":"1"}),
    ], style={"display":"flex","gap":"20px","marginBottom":"20px"})

    # ── Alertes recentes ──
    alertes_section = html.Div([
        html.Div("Alertes recentes", className="sga-card-title", style={"marginBottom":"12px"}),
        *(_alerte_rows(d["alertes"])),
    ], className="sga-card", style={"marginBottom":"20px"})

    # ── Concours ──
    if con:
        concours_section = html.Div([
            html.Div([
                html.Div("Concours en cours", style={"fontSize":"10px","letterSpacing":"3px",
                         "textTransform":"uppercase","color":"var(--muted)","marginBottom":"8px"}),
                html.Div(f"{con['nom']} {con['annee']}",
                         style={"fontFamily":"Times New Roman,serif","fontSize":"20px","fontWeight":"700","marginBottom":"16px"}),
                html.Div([
                    _kpi_mini(str(con["total"]),   "Candidats"),
                    _kpi_mini(str(con["payes"]),   "Paiements"),
                    _kpi_mini(str(con["valides"]), "Dossiers valides"),
                    _kpi_mini(str(con["admis"]),   "Admis"),
                ], style={"display":"grid","gridTemplateColumns":"repeat(4,1fr)","gap":"12px"}),
            ]),
        ], style={"padding":"20px","background":"var(--bg-card)","border":"1px solid var(--border)",
                  "borderRadius":"6px","marginBottom":"20px"})
    else:
        concours_section = html.Div()

    return html.Div([
        # Indicateurs academiques
        html.Div("Situation academique", style={"fontSize":"10px","letterSpacing":"3px",
                 "textTransform":"uppercase","color":"var(--muted)","marginBottom":"12px"}),
        kpi_row1,
        graphiques,
        graphique_mois,
        classement,
        alertes_section,

        # Separateur
        html.Hr(style={"border":"none","borderTop":"1px solid var(--border)","margin":"8px 0 24px"}),

        # Financier
        fin_section,

        # Concours
        concours_section,
    ])




def _alerte_rows(alertes):
    if not alertes:
        return [html.Div("Aucune alerte active.", style={"color":GREEN,"padding":"16px","fontSize":"13px"})]
    rows = []
    for a in alertes:
        rows.append(html.Div([
            html.Div(style={"width":"8px","height":"8px","borderRadius":"50%","flexShrink":"0",
                            "background":RED if a.type == "absence" else COPPER,
                            "marginTop":"4px"}),
            html.Div([
                html.Div(a.titre, style={"fontWeight":"600","fontSize":"13px"}),
                html.Div(a.message, style={"fontSize":"12px","color":"var(--muted)","lineHeight":"1.5"}),
            ]),
        ], style={"display":"flex","gap":"10px","padding":"10px 0",
                  "borderBottom":"1px solid var(--border)"}))
    return rows

def _top5_rows(top5):
    if not top5:
        return [html.Div("Aucune note.", style={"color":"var(--muted)","padding":"16px"})]
    return [student_row(s, m, i+1) for i, (s, m) in enumerate(top5)]


def _bottom5_rows(bottom5):
    en_diff = [(s, m) for s, m in bottom5 if m < 12]
    if not en_diff:
        return [html.Div("Tous les etudiants sont au-dessus de 12/20.",
                         style={"color":GREEN,"padding":"16px","fontSize":"13px"})]
    return [student_row(s, m) for s, m in en_diff]


def _kpi(val, label, color):
    return html.Div([
        html.Div(val, style={"fontFamily":"Times New Roman,serif","fontSize":"28px",
                             "fontWeight":"700","color":color,"lineHeight":"1.1","marginBottom":"4px"}),
        html.Div(label, style={"fontSize":"10px","color":"var(--muted)","letterSpacing":"1px",
                               "textTransform":"uppercase"}),
    ], style={"padding":"20px","background":"var(--bg-card)","border":"1px solid var(--border)",
              "borderRadius":"6px"})


def _kpi_mini(val, label):
    return html.Div([
        html.Div(val, style={"fontFamily":"JetBrains Mono,monospace","fontSize":"24px",
                             "fontWeight":"700","color":GOLD}),
        html.Div(label, style={"fontSize":"10px","color":"var(--muted)","letterSpacing":"1px"}),
    ], style={"padding":"12px","background":"var(--bg-secondary)","borderRadius":"4px"})
