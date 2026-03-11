import dash
from dash import html, dcc, Input, Output, State, callback, ALL
import plotly.graph_objects as go
from database import SessionLocal
from models import Classe, Course, Session, Student, Attendance
from datetime import date

dash.register_page(__name__, path="/presences", name="Presences")

def layout():
    db = SessionLocal()
    opts = [{"label":f"{c.code} - {c.libelle}","value":c.code} for c in db.query(Course).all()]
    db.close()
    db2 = SessionLocal()
    classes = db2.query(Classe).filter_by(actif=True).order_by(Classe.nom).all()
    classe_opts = [{"label": c.nom, "value": c.id} for c in classes]
    db2.close()
    return html.Div([
        dcc.Store(id="pres-classe-opts", data=classe_opts),
        html.Div([
            html.Div([html.Div("Cahier de Texte & Presences", className="page-title"),
                      html.Div("Enregistrement des seances - Appel numerique", className="page-subtitle")]),
        ], className="topbar"),

        html.Div([
            html.Div([
                html.Div("Nouvelle seance", className="sga-card-title", style={"marginBottom":"20px"}),
                html.Div([
                    html.Div([html.Span("Cours", className="sga-label"),
                              dcc.Dropdown(id="dd-cp", options=opts, placeholder="Selectionner un cours")
                          ]),
                          html.Div([html.Label("Classe", style={"fontSize":"12px","color":"var(--muted)","marginBottom":"4px"}),
                          dcc.Dropdown(id="dd-classe-pres", placeholder="Toutes les classes", clearable=True)]),
                    html.Div([html.Span("Date", className="sga-label"),
                              dcc.DatePickerSingle(id="dp-date", date=str(date.today()), display_format="DD/MM/YYYY")]),
                    html.Div([html.Span("Duree (h)", className="sga-label"),
                              dcc.Input(id="inp-dur", type="number", min=0.5, step=0.5, placeholder="2.0",
                                        className="sga-input", style={"width":"100%"})]),
                ], style={"display":"grid","gridTemplateColumns":"2fr 1fr 1fr","gap":"16px","marginBottom":"16px"}),
                html.Div([html.Span("Theme / Contenu", className="sga-label"),
                          dcc.Input(id="inp-theme", placeholder="Chapitre 3...",
                                    className="sga-input", style={"width":"100%"})], style={"marginBottom":"16px"}),
                html.Div(id="zone-appel"),
                html.Button("Enregistrer la seance", id="btn-save-sess",
                            className="btn-sga btn-green", style={"marginTop":"16px"}),
                html.Div(id="fb-sess"),
            ], className="sga-card", style={"flex":"1.2"}),

            html.Div([
                html.Div("Stats absences", className="sga-card-title", style={"marginBottom":"12px"}),
                dcc.Graph(id="ch-abs", config={"displayModeBar":False}, style={"height":"180px"}),
                html.Hr(style={"borderColor":"var(--border)","margin":"12px 0"}),
                html.Div("Dernieres seances", className="sga-card-title", style={"marginBottom":"10px"}),
                html.Div(id="recent-sess"),
            ], className="sga-card", style={"flex":"1"}),
        ], style={"display":"flex","gap":"20px","marginBottom":"24px"}),

        html.Div([
            html.Div([
                html.Span("Historique", className="sga-card-title"),
                dcc.Dropdown(id="dd-filter", options=opts, placeholder="Filtrer...",
                             clearable=True, style={"width":"260px"}),
            ], style={"display":"flex","justifyContent":"space-between","alignItems":"center","marginBottom":"16px"}),
            html.Div(id="hist-table"),
        ], className="sga-card"),

        dcc.Interval(id="iv-pres", interval=3000, max_intervals=1),
    ])


@callback(Output("dd-classe-pres","options"), Input("pres-classe-opts","data"))
def load_classe_opts_pres(data): return data or []


@callback(Output("zone-appel","children"), Input("dd-cp","value"))
def gen_checklist(code):
    if not code:
        return html.Div("Selectionnez un cours pour l appel.", style={"color":"var(--text-muted)","fontSize":"12px"})
    db = SessionLocal()
    students = [(s.id, s.nom, s.prenom) for s in db.query(Student).filter_by(actif=True).order_by(Student.nom).all()]
    db.close()
    return html.Div([
        html.Div([
            html.Span("Liste d appel - Cocher les ABSENTS", className="sga-label"),
            html.Span(f"{len(students)} etudiants", style={"fontSize":"11px","color":"var(--text-muted)"}),
        ], style={"display":"flex","justifyContent":"space-between","marginBottom":"10px"}),
        html.Div([
            html.Div(
                dcc.Checklist(id={"type":"abs","index":sid},
                              options=[{"label":f"  {nom} {prenom}","value":sid}],
                              value=[]),
            style={"padding":"8px 12px","borderRadius":"6px","background":"var(--bg-secondary)",
                   "border":"1px solid var(--border)"})
            for sid, nom, prenom in students
        ], style={"display":"grid","gridTemplateColumns":"1fr 1fr","gap":"6px",
                  "maxHeight":"180px","overflowY":"auto"}),
    ])

@callback(Output("fb-sess","children"), Output("recent-sess","children"),
          Input("btn-save-sess","n_clicks"),
          State("dd-cp","value"), State("dp-date","date"), State("inp-dur","value"),
          State("inp-theme","value"), State({"type":"abs","index":ALL},"value"),
          prevent_initial_call=True)
def save_sess(n,code,dv,dur,theme,abs_lists):
    if not all([code,dv,dur]):
        return html.Div("Cours, date et duree obligatoires.", className="sga-alert sga-alert-warning"), load_recent()
    absents = [v for sl in abs_lists for v in sl]
    db = SessionLocal()
    try:
        from datetime import datetime
        sess = Session(course_code=code, date=datetime.strptime(dv,"%Y-%m-%d").date(),
                       duree=float(dur), theme=theme)
        db.add(sess); db.flush()
        for sid in absents: db.add(Attendance(id_session=sess.id, id_student=sid))
        db.commit()

        # ── Notifications push automatiques ──────────────────────────────
        try:
            from notif_service import push_absence
            from models import Session as _Sess, Attendance as _Att
            db2 = SessionLocal()
            all_sess = db2.query(_Sess).filter_by(course_code=code).all()
            nb_sess  = len(all_sess)
            sess_ids = {s.id for s in all_sess}
            for sid in absents:
                nb_abs = db2.query(_Att).filter(
                    _Att.id_student == sid,
                    _Att.id_session.in_(sess_ids)
                ).count()
                taux = round(nb_abs / nb_sess * 100, 1) if nb_sess else 0
                if taux > 20:
                    push_absence(sid, code, nb_abs, nb_sess, taux)
            db2.close()
        except Exception:
            pass  # Ne pas bloquer l'enregistrement si notif échoue

        msg = html.Div(f"{len(absents)} absent(s) enregistre(s).", className="sga-alert sga-alert-success")
    except Exception as e:
        db.rollback(); msg = html.Div(str(e), className="sga-alert sga-alert-danger")
    finally:
        db.close()
    return msg, load_recent()

def load_recent():
    db = SessionLocal()
    sessions = db.query(Session).order_by(Session.date.desc()).limit(5).all()
    data = [(s.date, s.course_code, s.theme, len(s.attendances)) for s in sessions]
    db.close()
    if not data:
        return html.Div("Aucune seance.", style={"color":"var(--text-muted)","fontSize":"12px"})
    return html.Div([
        html.Div([
            html.Div(d.strftime("%d/%m"), style={"color":"var(--cyan)","fontWeight":"700","fontSize":"12px","minWidth":"40px"}),
            html.Div([
                html.Div(code, style={"fontWeight":"600","fontSize":"12px"}),
                html.Div((theme or "---")[:40], style={"fontSize":"10px","color":"var(--text-muted)"}),
            ]),
            html.Span(f"{nb_abs} abs.", style={"marginLeft":"auto","fontSize":"10px",
                      "color":"var(--red)" if nb_abs>0 else "var(--green)"}),
        ], style={"display":"flex","gap":"10px","alignItems":"center",
                  "padding":"8px 0","borderBottom":"1px solid rgba(255,255,255,0.04)"})
        for d, code, theme, nb_abs in data
    ])

@callback(Output("ch-abs","figure"), Output("hist-table","children"),
          Input("dd-filter","value"), Input("iv-pres","n_intervals"))
def update_panel(code,_):
    db = SessionLocal()
    courses  = db.query(Course).all()
    sessions = db.query(Session).all()
    attendances = db.query(Attendance).all()

    # Calculer absences par cours dans la session
    abs_by_course = {}
    for c in courses:
        sess_ids = {s.id for s in sessions if s.course_code == c.code}
        abs_by_course[c.code] = sum(1 for a in attendances if a.id_session in sess_ids)

    course_list = [(c.code, c.libelle, c.couleur or "#00d4ff") for c in courses]

    query = db.query(Session).order_by(Session.date.desc())
    if code: query = query.filter(Session.course_code==code)
    sess_list = query.limit(30).all()
    sess_data = [(s.date, s.course_code, s.duree, s.theme,
                  sum(1 for a in attendances if a.id_session==s.id)) for s in sess_list]
    db.close()

    fig = go.Figure(go.Bar(
        x=[c[0] for c in course_list],
        y=[abs_by_course.get(c[0],0) for c in course_list],
        marker=dict(color=[c[2] for c in course_list], line=dict(color="rgba(0,0,0,0)",width=0)),
        hovertemplate="<b>%{x}</b><br>Absences: %{y}<extra></extra>",
    ))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="JetBrains Mono",color="#64748b",size=10),
                      margin=dict(l=0,r=0,t=0,b=0),showlegend=False,
                      xaxis=dict(gridcolor="rgba(184,146,42,0.1)"),
                      yaxis=dict(gridcolor="rgba(184,146,42,0.1)"))

    if not sess_data:
        tbl = html.Div("Aucune seance.", style={"color":"var(--text-muted)","textAlign":"center","padding":"24px"})
    else:
        rows = [html.Tr([
            html.Td(d.strftime("%d/%m/%Y")),
            html.Td(html.Span(code, style={"color":"var(--cyan)","fontWeight":"600"})),
            html.Td(f"{dur}h"),
            html.Td(theme or "---", style={"color":"var(--text-muted)"}),
            html.Td(html.Span(f"{nb} absent(s)",
                    style={"color":"var(--red)" if nb>0 else "var(--green)","fontWeight":"600"})),
        ]) for d, code, dur, theme, nb in sess_data]
        tbl = html.Table(
            [html.Thead(html.Tr([html.Th(h) for h in ["Date","Cours","Duree","Theme","Absences"]])),
             html.Tbody(rows)],
            className="sga-table", style={"width":"100%"})
    return fig, tbl
