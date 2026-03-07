import dash
from dash import html, dcc, Input, Output, callback
import plotly.graph_objects as go
from database import SessionLocal
from models import Student, Course, Grade, Session, Attendance

dash.register_page(__name__, path="/analytics", name="Analytics")

T = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="JetBrains Mono", color="#8A8070", size=11),
    margin=dict(l=10, r=10, t=30, b=10),
    xaxis=dict(gridcolor="rgba(184,146,42,0.12)", linecolor="rgba(184,146,42,0.2)", tickfont=dict(color="#8A8070")),
    yaxis=dict(gridcolor="rgba(184,146,42,0.12)", linecolor="rgba(184,146,42,0.2)", tickfont=dict(color="#8A8070")),
)

def layout():
    return html.Div([
        html.Div([
            html.Div([html.Div("Analytics", className="page-title"),
                      html.Div("Analyse avancee des donnees academiques", className="page-subtitle")]),
        ], className="topbar"),

        html.Div([
            html.Div([
                html.Div("Distribution par cours (Violin)", className="sga-card-title", style={"marginBottom":"12px"}),
                dcc.Graph(id="an-violin", config={"displayModeBar":False}, style={"height":"300px"}),
            ], className="sga-card", style={"flex":"1.5"}),
            html.Div([
                html.Div("Scatter: Absences vs Moyenne", className="sga-card-title", style={"marginBottom":"12px"}),
                dcc.Graph(id="an-scatter", config={"displayModeBar":False}, style={"height":"300px"}),
            ], className="sga-card", style={"flex":"1"}),
        ], style={"display":"flex","gap":"20px","marginBottom":"20px"}),

        html.Div([
            html.Div([
                html.Div("Timeline volume horaire cumule", className="sga-card-title", style={"marginBottom":"12px"}),
                dcc.Graph(id="an-timeline", config={"displayModeBar":False}, style={"height":"280px"}),
            ], className="sga-card", style={"flex":"2"}),
            html.Div([
                html.Div("Repartition des mentions", className="sga-card-title", style={"marginBottom":"12px"}),
                dcc.Graph(id="an-pie", config={"displayModeBar":False}, style={"height":"280px"}),
            ], className="sga-card", style={"flex":"1"}),
        ], style={"display":"flex","gap":"20px"}),

        dcc.Interval(id="iv-an", interval=3000, max_intervals=1),
    ])

def _hr(hx):
    hx = hx.lstrip("#")
    return f"{int(hx[0:2],16)},{int(hx[2:4],16)},{int(hx[4:6],16)}"

@callback(
    Output("an-violin","figure"), Output("an-scatter","figure"),
    Output("an-timeline","figure"), Output("an-pie","figure"),
    Input("iv-an","n_intervals"),
)
def build(_):
    db = SessionLocal()
    courses     = db.query(Course).all()
    students    = db.query(Student).all()
    grades      = db.query(Grade).all()
    sessions    = db.query(Session).order_by(Session.date).all()
    attendances = db.query(Attendance).all()

    # Extraire toutes les donnees brutes dans la session
    course_data = [(c.code, c.libelle, c.couleur or "#00d4ff") for c in courses]
    grade_data  = [(g.course_code, g.note, g.id_student, g.coefficient) for g in grades]
    sess_data   = [(s.id, s.course_code, s.date, s.duree) for s in sessions]
    att_data    = [(a.id_session, a.id_student) for a in attendances]
    stu_data    = [(s.id, s.nom) for s in students]
    db.close()

    # Violin
    fig_v = go.Figure()
    for code, lib, col in course_data:
        notes = [n for c, n, sid, coef in grade_data if c == code]
        if notes:
            fig_v.add_trace(go.Violin(
                y=notes, name=code,
                fillcolor=f"rgba({_hr(col)},0.2)", line_color=col,
                box_visible=True, meanline_visible=True,
                points="all", pointpos=0,
                marker=dict(size=4, color=col, opacity=0.6),
            ))
    fig_v.update_layout(**T, showlegend=False, violingap=0.3)
    fig_v.update_yaxes(range=[0,20])

    # Scatter absences vs moyenne
    scatter = []
    for sid, nom in stu_data:
        g = [(n, coef) for _, n, s, coef in grade_data if s == sid]
        tc = sum(coef for _, coef in g)
        moy = round(sum(n*c for n,c in g)/tc, 2) if tc else None
        nb_abs = sum(1 for s_id, st_id in att_data if st_id == sid)
        if moy: scatter.append((nom, moy, nb_abs))

    fig_s = go.Figure(go.Scatter(
        x=[d[2] for d in scatter], y=[d[1] for d in scatter],
        mode="markers+text",
        text=[d[0] for d in scatter], textposition="top center",
        textfont=dict(size=9, color="#64748b"),
        marker=dict(size=12,
            color=[d[1] for d in scatter],
            colorscale=[[0,"#ff4560"],[0.5,"#ff6b35"],[1,"#00ff88"]],
            showscale=True,
            colorbar=dict(tickfont=dict(color="#64748b",size=9,family="JetBrains Mono"),bgcolor="rgba(0,0,0,0)"),
            line=dict(color="rgba(0,0,0,0.3)",width=1)),
        hovertemplate="<b>%{text}</b><br>Absences: %{x}<br>Moyenne: %{y:.2f}<extra></extra>",
    ))
    fig_s.update_layout(**T, showlegend=False)
    fig_s.update_yaxes(range=[0,20])

    # Timeline
    fig_t = go.Figure()
    for code, lib, col in course_data:
        c_sess = sorted([(s_id, d, dur) for s_id, c, d, dur in sess_data if c == code], key=lambda x: x[1])
        if c_sess:
            total=0; cumul=[]; dates=[]
            for _, d, dur in c_sess:
                total+=dur; cumul.append(total); dates.append(d)
            fig_t.add_trace(go.Scatter(
                x=dates, y=cumul, name=code,
                mode="lines+markers",
                line=dict(color=col, width=2), marker=dict(size=6, color=col),
                fill="tozeroy", fillcolor=f"rgba({_hr(col)},0.05)",
                hovertemplate=f"<b>{code}</b><br>%{{x}}<br>%{{y}}h cumules<extra></extra>",
            ))
    fig_t.update_layout(**T, legend=dict(font=dict(color="#64748b",size=10,family="JetBrains Mono"),bgcolor="rgba(0,0,0,0)"))

    # Donut mentions
    m = {"TB (16+)":0,"B (14-16)":0,"AB (12-14)":0,"P (10-12)":0,"F (<10)":0}
    for _, n, _, _ in grade_data:
        if n>=16: m["TB (16+)"]+=1
        elif n>=14: m["B (14-16)"]+=1
        elif n>=12: m["AB (12-14)"]+=1
        elif n>=10: m["P (10-12)"]+=1
        else: m["F (<10)"]+=1

    fig_p = go.Figure(go.Pie(
        labels=list(m.keys()), values=list(m.values()), hole=0.6,
        marker=dict(colors=["#00ff88","#00d4ff","#a855f7","#ff6b35","#ff4560"],
                    line=dict(color="#0a0e1a",width=2)),
        textfont=dict(family="JetBrains Mono",size=10),
        hovertemplate="<b>%{label}</b><br>%{value} notes (%{percent})<extra></extra>",
    ))
    fig_p.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="JetBrains Mono",color="#64748b",size=11),
        margin=dict(l=0,r=0,t=0,b=0), showlegend=True,
        legend=dict(font=dict(color="#e2e8f0",size=10,family="JetBrains Mono"),bgcolor="rgba(0,0,0,0)"),
    )
    fig_p.add_annotation(text="Mentions",x=0.5,y=0.5,showarrow=False,
                         font=dict(color="#64748b",size=12,family="Rajdhani"))
    return fig_v, fig_s, fig_t, fig_p
