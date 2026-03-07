import dash
from dash import html, dcc, Input, Output, State, callback, ctx
from database import SessionLocal
from models import Course, Session
from datetime import date, timedelta
import calendar

dash.register_page(__name__, path="/calendrier", name="Calendrier")

MOIS_FR = ["","Janvier","Février","Mars","Avril","Mai","Juin",
           "Juillet","Août","Septembre","Octobre","Novembre","Décembre"]
JOURS_FR = ["Lun","Mar","Mer","Jeu","Ven","Sam","Dim"]

def layout():
    today = date.today()
    return html.Div([
        html.Div([
            html.Div([
                html.Div("Calendrier des Séances", className="page-title"),
                html.Div("Visualisation et planification mensuelle", className="page-subtitle"),
            ]),
            html.Div([
                html.Button("◀", id="cal-prev", className="btn-sga btn-gold",
                            style={"padding":"8px 16px","fontSize":"16px"}),
                html.Div(id="cal-titre", style={
                    "fontFamily":"Times New Roman,serif","fontSize":"22px",
                    "fontWeight":"700","color":"var(--text-primary)",
                    "minWidth":"200px","textAlign":"center","letterSpacing":"2px",
                }),
                html.Button("▶", id="cal-next", className="btn-sga btn-gold",
                            style={"padding":"8px 16px","fontSize":"16px"}),
                html.Button("Aujourd'hui", id="cal-today", className="btn-sga btn-green",
                            style={"marginLeft":"12px","fontSize":"11px"}),
            ], style={"display":"flex","alignItems":"center","gap":"12px"}),
        ], className="topbar"),

        html.Div([
            # Calendrier principal
            html.Div([
                html.Div(id="cal-grid"),
            ], className="sga-card", style={"flex":"2"}),

            # Panneau latéral
            html.Div([
                # Légende cours
                html.Div([
                    html.Div("Cours", className="sga-card-title",
                             style={"marginBottom":"14px"}),
                    html.Div(id="cal-legende"),
                ], className="sga-card", style={"marginBottom":"20px"}),

                # Détail jour sélectionné
                html.Div([
                    html.Div("Séances du jour", className="sga-card-title",
                             style={"marginBottom":"14px"}),
                    html.Div(id="cal-detail-jour",
                             style={"color":"var(--muted)","fontSize":"13px"}),
                ], className="sga-card", style={"marginBottom":"20px"}),

                # Planifier une séance
                html.Div([
                    html.Div("Planifier une séance", className="sga-card-title",
                             style={"marginBottom":"16px"}),
                    html.Div([
                        html.Span("Cours", className="sga-label"),
                        dcc.Dropdown(id="plan-cours", placeholder="Cours…",
                                     clearable=False),
                    ], style={"marginBottom":"12px"}),
                    html.Div([
                        html.Span("Date", className="sga-label"),
                        dcc.Input(id="plan-date", type="text",
                                  placeholder="JJ/MM/AAAA",
                                  className="sga-input", style={"width":"100%"}),
                    ], style={"marginBottom":"12px"}),
                    html.Div([
                        html.Span("Durée (h)", className="sga-label"),
                        dcc.Input(id="plan-duree", type="number",
                                  value=2.0, min=0.5, step=0.5,
                                  className="sga-input", style={"width":"100%"}),
                    ], style={"marginBottom":"12px"}),
                    html.Div([
                        html.Span("Thème", className="sga-label"),
                        dcc.Input(id="plan-theme", placeholder="Optionnel…",
                                  className="sga-input", style={"width":"100%"}),
                    ], style={"marginBottom":"16px"}),
                    html.Button("+ Planifier", id="btn-planifier",
                                className="btn-sga btn-gold",
                                style={"width":"100%","justifyContent":"center"}),
                    html.Div(id="plan-feedback", style={"marginTop":"10px"}),
                ], className="sga-card"),
            ], style={"width":"280px","flexShrink":"0"}),
        ], style={"display":"flex","gap":"20px","alignItems":"flex-start"}),

        dcc.Store(id="cal-mois",  data=date.today().month),
        dcc.Store(id="cal-annee", data=date.today().year),
        dcc.Store(id="cal-jour-sel", data=None),
    ])


# ── Navigation mois ───────────────────────────────────────────────────────────
@callback(
    Output("cal-mois",  "data"),
    Output("cal-annee", "data"),
    Input("cal-prev",   "n_clicks"),
    Input("cal-next",   "n_clicks"),
    Input("cal-today",  "n_clicks"),
    State("cal-mois",   "data"),
    State("cal-annee",  "data"),
    prevent_initial_call=True,
)
def nav_mois(prev, nxt, today_btn, mois, annee):
    t = ctx.triggered_id
    if t == "cal-today":
        return date.today().month, date.today().year
    if t == "cal-prev":
        mois -= 1
        if mois < 1: mois, annee = 12, annee - 1
    if t == "cal-next":
        mois += 1
        if mois > 12: mois, annee = 1, annee + 1
    return mois, annee


# ── Rendu du calendrier ───────────────────────────────────────────────────────
@callback(
    Output("cal-grid",    "children"),
    Output("cal-titre",   "children"),
    Output("cal-legende", "children"),
    Output("plan-cours",  "options"),
    Input("cal-mois",     "data"),
    Input("cal-annee",    "data"),
    Input("plan-feedback","children"),   # refresh après ajout
)
def render_calendrier(mois, annee, _):
    db = SessionLocal()
    courses  = db.query(Course).all()
    sessions = db.query(Session).all()
    course_map = {c.code: c for c in courses}
    db.close()

    today = date.today()

    # Sessions de ce mois
    sess_du_mois = {}
    for s in sessions:
        if s.date.month == mois and s.date.year == annee:
            sess_du_mois.setdefault(s.date.day, []).append(s)

    # Grille calendrier
    cal = calendar.monthcalendar(annee, mois)

    # En-têtes jours
    header = html.Div([
        html.Div(j, style={
            "textAlign":"center","padding":"10px 0",
            "fontFamily":"JetBrains Mono,monospace","fontSize":"11px",
            "letterSpacing":"2px","textTransform":"uppercase",
            "color":"var(--gold)" if j in ("Sam","Dim") else "var(--muted)",
            "fontWeight":"600",
        }) for j in JOURS_FR
    ], style={"display":"grid","gridTemplateColumns":"repeat(7,1fr)",
              "borderBottom":"1px solid var(--border)","marginBottom":"4px"})

    rows = []
    for semaine in cal:
        cells = []
        for jour in semaine:
            if jour == 0:
                cells.append(html.Div(style={"minHeight":"80px"}))
                continue
            d = date(annee, mois, jour)
            is_today    = (d == today)
            is_weekend  = (d.weekday() >= 5)
            seances_j   = sess_du_mois.get(jour, [])

            # Pastilles séances
            pastilles = []
            for s in seances_j[:3]:
                c = course_map.get(s.course_code)
                col = c.couleur if c else "#B8922A"
                pastilles.append(html.Div(
                    s.course_code,
                    style={
                        "background": col,
                        "color": "#1E1A12",
                        "fontSize": "9px","fontWeight":"700",
                        "fontFamily":"JetBrains Mono,monospace",
                        "padding": "2px 6px","borderRadius":"3px",
                        "marginBottom":"2px","letterSpacing":"1px",
                        "overflow":"hidden","whiteSpace":"nowrap",
                    }
                ))
            if len(seances_j) > 3:
                pastilles.append(html.Div(f"+{len(seances_j)-3}",
                    style={"fontSize":"9px","color":"var(--muted)"}))

            cells.append(html.Div([
                html.Div(str(jour), style={
                    "fontFamily":"Times New Roman,serif",
                    "fontSize":"16px","fontWeight":"700" if is_today else "400",
                    "color":"var(--gold)" if is_today else
                            "var(--muted)" if is_weekend else "var(--text-primary)",
                    "marginBottom":"4px",
                    "background":"var(--gold)" if is_today else "transparent",
                    "width":"28px","height":"28px","borderRadius":"50%",
                    "display":"flex","alignItems":"center","justifyContent":"center",
                    "color":"var(--bg-primary)" if is_today else
                            "var(--muted)" if is_weekend else "var(--text-primary)",
                }),
                *pastilles,
            ],
            id={"type":"cal-jour","index":f"{annee}-{mois:02d}-{jour:02d}"},
            n_clicks=0,
            style={
                "minHeight":"80px","padding":"8px","borderRadius":"4px",
                "border":"1px solid transparent","cursor":"pointer",
                "background":"rgba(184,146,42,0.06)" if is_today else "transparent",
                "transition":"background 0.15s, border 0.15s",
            }))

        rows.append(html.Div(cells,
            style={"display":"grid","gridTemplateColumns":"repeat(7,1fr)","gap":"2px"}))

    grid = html.Div([header, *rows])
    titre = f"{MOIS_FR[mois]} {annee}"

    # Légende
    legende = html.Div([
        html.Div([
            html.Div(style={"width":"12px","height":"12px","borderRadius":"2px","flexShrink":"0",
                            "background":c.couleur or "#B8922A"}),
            html.Div(c.code, style={"fontSize":"11px","fontFamily":"JetBrains Mono,monospace",
                                     "fontWeight":"600","color":"var(--text-primary)"}),
            html.Div(c.libelle[:18], style={"fontSize":"11px","color":"var(--muted)"}),
        ], style={"display":"flex","gap":"8px","alignItems":"center","padding":"6px 0",
                  "borderBottom":"1px solid rgba(30,26,18,0.06)"})
        for c in courses
    ])

    opts = [{"label":f"{c.code} — {c.libelle}","value":c.code} for c in courses]
    return grid, titre, legende, opts


# ── Détail jour cliqué ────────────────────────────────────────────────────────
@callback(
    Output("cal-detail-jour", "children"),
    Output("plan-date",       "value"),
    Output("cal-jour-sel",    "data"),
    Input({"type":"cal-jour","index":dash.ALL}, "n_clicks"),
    State({"type":"cal-jour","index":dash.ALL}, "id"),
    prevent_initial_call=True,
)
def detail_jour(clicks, ids):
    if not ctx.triggered_id: return "Cliquez sur un jour.", "", None
    date_str = ctx.triggered_id["index"]  # "AAAA-MM-JJ"
    try:
        d = date.fromisoformat(date_str)
    except Exception:
        return "Date invalide.", "", None

    db = SessionLocal()
    sessions  = db.query(Session).all()
    courses   = db.query(Course).all()
    course_map = {c.code: c for c in courses}
    seances_j = [s for s in sessions if s.date == d]
    db.close()

    if not seances_j:
        contenu = html.Div([
            html.Div(d.strftime("%A %d %B").capitalize(),
                     style={"fontFamily":"Times New Roman,serif","fontWeight":"700",
                            "fontSize":"16px","marginBottom":"8px"}),
            html.Div("Aucune séance ce jour.",
                     style={"color":"var(--muted)","fontSize":"13px"}),
        ])
    else:
        items = []
        for s in seances_j:
            c = course_map.get(s.course_code)
            col = c.couleur if c else "#B8922A"
            items.append(html.Div([
                html.Div(style={"width":"4px","background":col,
                                "borderRadius":"2px","flexShrink":"0"}),
                html.Div([
                    html.Div(s.course_code, style={"fontWeight":"700","fontSize":"13px",
                                                    "color":"var(--text-primary)"}),
                    html.Div(s.theme or "—", style={"fontSize":"12px","color":"var(--muted)"}),
                    html.Div(f"{s.duree}h", style={"fontSize":"11px","color":col,
                             "fontFamily":"JetBrains Mono,monospace"}),
                ]),
            ], style={"display":"flex","gap":"10px","padding":"10px",
                      "background":"var(--bg-secondary)","borderRadius":"4px",
                      "marginBottom":"8px"}))
        contenu = html.Div([
            html.Div(d.strftime("%A %d %B").capitalize(),
                     style={"fontFamily":"Times New Roman,serif","fontWeight":"700",
                            "fontSize":"16px","marginBottom":"12px"}),
            *items,
        ])

    date_affiche = d.strftime("%d/%m/%Y")
    return contenu, date_affiche, date_str


# ── Planifier une séance ──────────────────────────────────────────────────────
@callback(
    Output("plan-feedback", "children"),
    Input("btn-planifier",  "n_clicks"),
    State("plan-cours",     "value"),
    State("plan-date",      "value"),
    State("plan-duree",     "value"),
    State("plan-theme",     "value"),
    prevent_initial_call=True,
)
def planifier(n, code, date_str, duree, theme):
    if not code or not date_str or not duree:
        return html.Div("Cours, date et durée requis.",
                        className="sga-alert sga-alert-warning")
    try:
        from datetime import datetime
        d = datetime.strptime(date_str.strip(), "%d/%m/%Y").date()
    except Exception:
        return html.Div("Format de date invalide (JJ/MM/AAAA).",
                        className="sga-alert sga-alert-danger")
    db = SessionLocal()
    try:
        db.add(Session(course_code=code, date=d,
                       duree=float(duree), theme=theme or ""))
        db.commit()
        return html.Div(f"✓ Séance {code} planifiée le {date_str}.",
                        className="sga-alert sga-alert-success")
    except Exception as e:
        db.rollback()
        return html.Div(str(e), className="sga-alert sga-alert-danger")
    finally:
        db.close()
