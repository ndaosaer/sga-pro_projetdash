import dash
from dash import html, dcc, Input, Output, callback
import plotly.graph_objects as go
from database import SessionLocal
from models import Student, Course, Session, Grade, Notification, Attendance
from datetime import date
from sqlalchemy import func

dash.register_page(__name__, path="/", name="Dashboard")

T = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="JetBrains Mono", color="#8A8070", size=11),
    margin=dict(l=10, r=10, t=30, b=10),
    xaxis=dict(gridcolor="rgba(184,146,42,0.12)", linecolor="rgba(184,146,42,0.2)", tickfont=dict(color="#8A8070")),
    yaxis=dict(gridcolor="rgba(184,146,42,0.12)", linecolor="rgba(184,146,42,0.2)", tickfont=dict(color="#8A8070")),
)

def layout():
    db = SessionLocal()
    nb_students = db.query(Student).filter_by(actif=True).count()
    nb_courses  = db.query(Course).count()
    nb_sessions = db.query(Session).count()
    grades      = db.query(Grade).all()
    notes       = [g.note for g in grades]
    avg_global  = round(sum(notes)/len(notes), 2) if notes else 0
    notifs      = db.query(Notification).filter_by(lu=False).order_by(Notification.created_at.desc()).limit(5).all()
    notif_data  = [(n.type, n.titre, n.message, n.created_at) for n in notifs]
    db.close()

    return html.Div([
        html.Div([
            html.Div([
                html.Div("Dashboard", className="page-title"),
                html.Div("Vue d ensemble - Tableau de bord", className="page-subtitle"),
            ]),
            html.Div(date.today().strftime("%d %b %Y"),
                     style={"color":"var(--cyan)","fontSize":"12px","letterSpacing":"2px","fontWeight":"600"}),
        ], className="topbar"),

        html.Div([
            _kpi(str(nb_students), "Etudiants actifs",     "kpi-cyan"),
            _kpi(str(nb_courses),  "Cours dispenses",      "kpi-green"),
            _kpi(str(nb_sessions), "Seances enregistrees", "kpi-orange"),
            _kpi(str(avg_global),  "Moyenne generale /20", "kpi-purple"),
        ], style={"display":"grid","gridTemplateColumns":"repeat(4,1fr)","gap":"20px","marginBottom":"24px"}),

        html.Div([
            html.Div([
                html.Div("Moyennes par cours", className="sga-card-title", style={"marginBottom":"12px"}),
                dcc.Graph(id="ch-moyennes", config={"displayModeBar":False}, style={"height":"260px"}),
            ], className="sga-card", style={"flex":"2"}),
            html.Div([
                html.Div("Distribution des notes", className="sga-card-title", style={"marginBottom":"12px"}),
                dcc.Graph(id="ch-distrib", config={"displayModeBar":False}, style={"height":"260px"}),
            ], className="sga-card", style={"flex":"1"}),
        ], style={"display":"flex","gap":"20px","marginBottom":"20px"}),

        html.Div([
            html.Div([
                html.Div("Progression des cours", className="sga-card-title", style={"marginBottom":"12px"}),
                dcc.Graph(id="ch-progr", config={"displayModeBar":False}, style={"height":"220px"}),
            ], className="sga-card", style={"flex":"1.5"}),
            html.Div([
                html.Div("Heatmap Absences", className="sga-card-title", style={"marginBottom":"12px"}),
                dcc.Graph(id="ch-heat", config={"displayModeBar":False}, style={"height":"220px"}),
            ], className="sga-card", style={"flex":"1.5"}),
            html.Div([
                html.Div("Alertes systeme", className="sga-card-title", style={"marginBottom":"12px"}),
                html.Div([_notif(*n) for n in notif_data] or [
                    html.Div("Aucune alerte", style={"color":"var(--text-muted)","fontSize":"12px"})
                ]),
            ], className="sga-card", style={"flex":"1"}),
        ], style={"display":"flex","gap":"20px"}),

        dcc.Interval(id="iv-dash", interval=60000),
    ])

def _kpi(value, label, cls):
    return html.Div([
        html.Div(value, className="kpi-value"),
        html.Div(label, className="kpi-label"),
    ], className=f"kpi-card {cls}")

def _notif(type_, titre, message, created_at):
    colors = {"warning":"#ff6b35","danger":"#ff4560","info":"#00d4ff","success":"#00ff88"}
    return html.Div([
        html.Div(style={"backgroundColor":colors.get(type_,"#64748b")}, className="notif-dot"),
        html.Div([
            html.Div(titre, className="notif-title"),
            html.Div(message[:55]+"..." if len(message)>55 else message, className="notif-msg"),
            html.Div(created_at.strftime("%d/%m %H:%M") if created_at else "", className="notif-time"),
        ]),
    ], className="notif-item")

@callback(
    Output("ch-moyennes","figure"), Output("ch-distrib","figure"),
    Output("ch-progr","figure"),    Output("ch-heat","figure"),
    Input("iv-dash","n_intervals"),
)
def update_charts(_):
    db = SessionLocal()

    # Recuperer toutes les donnees dans la session
    courses  = db.query(Course).all()
    students = db.query(Student).all()
    grades   = db.query(Grade).all()
    sessions = db.query(Session).all()
    attendances = db.query(Attendance).all()

    # Extraire les donnees brutes pendant que la session est ouverte
    course_data = [(c.code, c.libelle, c.volume_horaire, c.couleur or "#00d4ff") for c in courses]
    student_ids = [s.id for s in students[:8]]
    student_noms = [s.nom[:8] for s in students[:8]]
    grade_data  = [(g.course_code, g.note) for g in grades]
    session_data = [(s.course_code, s.duree) for s in sessions]
    att_data    = [(a.id_session, a.id_student) for a in attendances]
    sess_by_course = {}
    for s in sessions:
        sess_by_course.setdefault(s.course_code, []).append((s.id, s.duree))

    db.close()

    def hr(hx):
        hx = hx.lstrip("#")
        return f"{int(hx[0:2],16)},{int(hx[2:4],16)},{int(hx[4:6],16)}"

    # Chart 1 — barres moyennes
    fig1 = go.Figure()
    avgs = []
    for code, lib, vol, col in course_data:
        notes = [n for c, n in grade_data if c == code]
        if notes:
            avgs.append((lib[:14], round(sum(notes)/len(notes),2), col))
    if avgs:
        lbs, vs, cs = zip(*avgs)
        fig1.add_trace(go.Bar(
            x=list(lbs), y=list(vs),
            marker=dict(color=list(cs), opacity=0.85, line=dict(color="rgba(0,0,0,0)",width=0)),
            text=[f"{v:.1f}" for v in vs], textposition="outside",
            textfont=dict(color="#e2e8f0",size=10),
            hovertemplate="<b>%{x}</b><br>Moyenne: %{y:.2f}/20<extra></extra>",
        ))
    fig1.update_layout(**T, showlegend=False)
    fig1.update_yaxes(range=[0,22])

    # Chart 2 — histogramme
    all_notes = [n for _, n in grade_data]
    fig2 = go.Figure(go.Histogram(
        x=all_notes, nbinsx=18,
        marker=dict(color=all_notes,
            colorscale=[[0,"#ff4560"],[0.5,"#ff6b35"],[1,"#00ff88"]],
            line=dict(color="rgba(0,0,0,0.2)",width=0.5)),
        hovertemplate="Note: %{x}<br>Effectif: %{y}<extra></extra>",
    ))
    fig2.update_layout(**T, showlegend=False, bargap=0.06)

    # Chart 3 — progression
    fig3 = go.Figure()
    for code, lib, vol, col in course_data:
        heures = sum(d for c, d in session_data if c == code)
        prog   = min(round(heures/vol*100,1),100) if vol else 0
        fig3.add_trace(go.Bar(
            y=[lib[:16]], x=[prog], orientation="h",
            marker=dict(color=col, opacity=0.8, line=dict(color="rgba(0,0,0,0)",width=0)),
            text=[f"{prog}%"], textposition="inside",
            textfont=dict(color="#0a0e1a",size=10,family="JetBrains Mono"),
            hovertemplate=f"<b>{lib}</b><br>{heures:.1f}h / {vol}h<extra></extra>",
        ))
    fig3.update_layout(**T, showlegend=False, barmode="stack")
    fig3.update_xaxes(range=[0,100])

    # Chart 4 — heatmap
    z_data = []
    for sid in student_ids:
        row = []
        for code, lib, vol, col in course_data:
            sess_ids = [s_id for s_id, _ in sess_by_course.get(code, [])]
            absences = sum(1 for s_id, st_id in att_data if s_id in sess_ids and st_id == sid)
            total    = max(len(sess_ids), 1)
            row.append(round(absences/total*100,1))
        z_data.append(row)

    fig4 = go.Figure(go.Heatmap(
        z=z_data,
        x=[c[0] for c in course_data],
        y=student_noms,
        colorscale=[[0,"#131929"],[0.4,"#ff6b35"],[1,"#ff4560"]],
        hovertemplate="<b>%{y}</b> - %{x}<br>Taux: %{z:.1f}%<extra></extra>",
        showscale=True,
        colorbar=dict(tickfont=dict(color="#64748b",size=9,family="JetBrains Mono"),bgcolor="rgba(0,0,0,0)"),
    ))
    fig4.update_layout(**T)
    return fig1, fig2, fig3, fig4
