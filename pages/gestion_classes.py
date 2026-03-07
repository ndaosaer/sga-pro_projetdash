import dash
from dash import html, dcc, Input, Output, State, callback, ctx
from database import SessionLocal
from models import Classe, Niveau, Student, CoursClasse, Course
from datetime import datetime

dash.register_page(__name__, path="/classes", name="Classes")

COULEURS_PRESET = [
    "#2D6A3F","#B8922A","#8B5E3C","#1B4F72",
    "#6C3483","#1A5276","#784212","#1B6B50",
]


def layout():
    return html.Div([
        dcc.Store(id="cl-refresh", data=0),
        dcc.Store(id="cl-selected", data=None),

        html.Div([
            html.Div([
                html.Div("Gestion des Classes", className="page-title"),
                html.Div("Niveaux, filieres et affectation des etudiants",
                         className="page-subtitle"),
            ]),
            html.Button("+ Nouvelle classe", id="btn-cl-new",
                        n_clicks=0, className="btn-sga btn-gold"),
        ], className="topbar"),

        html.Div([
            # Grille des classes
            html.Div(id="cl-grid", style={"marginBottom":"24px"}),

            # Detail classe selectionnee
            html.Div(id="cl-detail"),
        ], style={"padding":"24px"}),

        # ── Modal nouvelle classe ──
        html.Div([
            html.Div([
                html.Div("Creer une classe", className="sga-card-title",
                         style={"marginBottom":"20px"}),
                html.Div([
                    html.Div([
                        html.Div("Niveau", className="sga-label"),
                        dcc.Dropdown(id="nc-niveau", placeholder="Licence / Master...",
                                     clearable=False),
                    ], style={"flex":"1"}),
                    html.Div([
                        html.Div("Filiere", className="sga-label"),
                        dcc.Input(id="nc-filiere", placeholder="ex: Statistique, Economie",
                                  className="sga-input", style={"width":"100%"}),
                    ], style={"flex":"2"}),
                ], style={"display":"flex","gap":"16px","marginBottom":"14px"}),
                html.Div([
                    html.Div([
                        html.Div("Nom complet", className="sga-label"),
                        dcc.Input(id="nc-nom", placeholder="ex: L3 Statistique",
                                  className="sga-input", style={"width":"100%"}),
                    ], style={"flex":"2"}),
                    html.Div([
                        html.Div("Code unique", className="sga-label"),
                        dcc.Input(id="nc-code", placeholder="ex: L3-STAT",
                                  className="sga-input", style={"width":"100%"}),
                    ], style={"flex":"1"}),
                ], style={"display":"flex","gap":"16px","marginBottom":"14px"}),
                html.Div([
                    html.Div([
                        html.Div("Annee academique", className="sga-label"),
                        dcc.Input(id="nc-annee", value="2025-2026",
                                  className="sga-input", style={"width":"100%"}),
                    ], style={"flex":"1"}),
                    html.Div([
                        html.Div("Effectif max", className="sga-label"),
                        dcc.Input(id="nc-effectif", type="number", value=40,
                                  className="sga-input", style={"width":"100%"}),
                    ], style={"flex":"1"}),
                    html.Div([
                        html.Div("Couleur", className="sga-label"),
                        dcc.Dropdown(id="nc-couleur",
                                     options=[{"label":c,"value":c} for c in COULEURS_PRESET],
                                     value=COULEURS_PRESET[0], clearable=False),
                    ], style={"flex":"1"}),
                ], style={"display":"flex","gap":"16px","marginBottom":"20px"}),
                html.Div([
                    html.Button("Creer", id="btn-nc-cl-save", n_clicks=0,
                                className="btn-sga btn-gold"),
                    html.Button("Annuler", id="btn-nc-cl-cancel", n_clicks=0,
                                className="btn-sga"),
                ], style={"display":"flex","gap":"10px"}),
                html.Div(id="nc-cl-feedback", style={"marginTop":"12px"}),
            ], style={"background":"var(--bg-card)","border":"1px solid var(--border)",
                      "borderRadius":"6px","padding":"32px","width":"560px","margin":"0 auto"}),
        ], id="modal-cl",
           style={"display":"none","position":"fixed","inset":"0",
                  "background":"rgba(0,0,0,0.5)","zIndex":"999",
                  "alignItems":"center","justifyContent":"center"}),
    ])


@callback(
    Output("nc-niveau","options"),
    Input("cl-refresh","data"),
)
def load_niveaux(r):
    db = SessionLocal()
    try:
        niveaux = db.query(Niveau).order_by(Niveau.ordre).all()
        return [{"label":f"{n.nom} ({n.abrev})","value":n.id} for n in niveaux]
    finally:
        db.close()


@callback(
    Output("modal-cl","style"),
    Input("btn-cl-new","n_clicks"),
    Input("btn-nc-cl-cancel","n_clicks"),
    Input("btn-nc-cl-save","n_clicks"),
    prevent_initial_call=True,
)
def toggle_modal(n1, n2, n3):
    show = {"display":"flex","position":"fixed","inset":"0","background":"rgba(0,0,0,0.5)",
            "zIndex":"999","alignItems":"center","justifyContent":"center"}
    if ctx.triggered_id == "btn-cl-new": return show
    return {"display":"none"}


@callback(
    Output("nc-cl-feedback","children"),
    Output("cl-refresh","data", allow_duplicate=True),
    Input("btn-nc-cl-save","n_clicks"),
    State("nc-niveau","value"), State("nc-filiere","value"),
    State("nc-nom","value"),    State("nc-code","value"),
    State("nc-annee","value"),  State("nc-effectif","value"),
    State("nc-couleur","value"),State("cl-refresh","data"),
    prevent_initial_call=True,
)
def creer_classe(n, niveau_id, filiere, nom, code, annee, effectif, couleur, refresh):
    if not all([niveau_id, nom, code]):
        return html.Div("Niveau, nom et code requis.",
                        className="sga-alert sga-alert-warning"), dash.no_update
    db = SessionLocal()
    try:
        cl = Classe()
        cl.nom = nom; cl.code = code.upper().replace(" ","-")
        cl.niveau_id = niveau_id; cl.filiere = filiere
        cl.annee = annee; cl.effectif_max = int(effectif or 40)
        cl.couleur = couleur; cl.actif = True
        cl.created_at = datetime.now()
        db.add(cl); db.commit()
        return html.Div("Classe creee.", className="sga-alert sga-alert-success"), (refresh or 0)+1
    except Exception as e:
        db.rollback()
        return html.Div(str(e), className="sga-alert sga-alert-danger"), dash.no_update
    finally:
        db.close()


@callback(
    Output("cl-grid","children"),
    Input("cl-refresh","data"),
)
def render_grid(r):
    db = SessionLocal()
    try:
        niveaux  = db.query(Niveau).order_by(Niveau.ordre).all()
        classes  = db.query(Classe).filter_by(actif=True).all()
        students = db.query(Student).filter_by(actif=True).all()
        stu_count = {}
        for s in students:
            if s.classe_id:
                stu_count[s.classe_id] = stu_count.get(s.classe_id, 0) + 1

        sections = []
        for niv in niveaux:
            cls_niv = [c for c in classes if c.niveau_id == niv.id]
            if not cls_niv: continue
            cards = []
            for cl in sorted(cls_niv, key=lambda x: x.nom):
                nb_etu  = stu_count.get(cl.id, 0)
                pct     = min(100, round(nb_etu / cl.effectif_max * 100)) if cl.effectif_max else 0
                col     = cl.couleur or "var(--gold)"
                cards.append(html.Div([
                    html.Div(style={"height":"4px","background":col,"borderRadius":"4px 4px 0 0"}),
                    html.Div([
                        html.Div([
                            html.Div(cl.code, style={"fontFamily":"JetBrains Mono,monospace",
                                     "fontSize":"11px","letterSpacing":"2px","color":col,
                                     "fontWeight":"700","marginBottom":"4px"}),
                            html.Div(cl.nom, style={"fontWeight":"700","fontSize":"14px",
                                     "marginBottom":"2px"}),
                            html.Div(cl.filiere or "", style={"fontSize":"11px","color":"var(--muted)"}),
                        ], style={"flex":"1"}),
                        html.Div([
                            html.Div(str(nb_etu), style={"fontFamily":"Times New Roman,serif",
                                     "fontSize":"32px","fontWeight":"700","color":col,
                                     "lineHeight":"1","textAlign":"right"}),
                            html.Div("etudiants", style={"fontSize":"9px","color":"var(--muted)",
                                     "textAlign":"right"}),
                        ]),
                    ], style={"display":"flex","alignItems":"flex-start",
                              "padding":"14px 16px","gap":"12px"}),
                    html.Div([
                        html.Div(style={"height":"4px","borderRadius":"2px",
                                        "background":"var(--border)","overflow":"hidden"},
                                 children=[html.Div(style={"height":"100%",
                                     "width":f"{pct}%","background":col,"borderRadius":"2px"})]),
                        html.Div(f"{nb_etu}/{cl.effectif_max} places",
                                 style={"fontSize":"10px","color":"var(--muted)",
                                        "marginTop":"4px","textAlign":"right"}),
                    ], style={"padding":"0 16px 12px"}),
                ], id={"type":"cl-card","index":cl.id},
                   n_clicks=0,
                   style={"background":"var(--bg-card)","border":"1px solid var(--border)",
                          "borderRadius":"6px","cursor":"pointer","overflow":"hidden",
                          "transition":"border-color 0.2s"}))

            sections.append(html.Div([
                html.Div(niv.nom.upper(), style={"fontSize":"10px","letterSpacing":"3px",
                         "textTransform":"uppercase","color":"var(--muted)","fontWeight":"700",
                         "marginBottom":"12px","paddingLeft":"4px"}),
                html.Div(cards, style={"display":"grid",
                         "gridTemplateColumns":"repeat(auto-fill,minmax(220px,1fr))",
                         "gap":"16px","marginBottom":"28px"}),
            ]))

        if not sections:
            return html.Div([
                html.Div("Aucune classe configuree.",
                         style={"textAlign":"center","color":"var(--muted)",
                                "padding":"60px","fontSize":"16px"}),
                html.Div("Cliquez sur '+ Nouvelle classe' ou lancez le script de peuplement.",
                         style={"textAlign":"center","color":"var(--muted)","fontSize":"12px"}),
            ])
        return html.Div(sections)
    finally:
        db.close()


@callback(
    Output("cl-selected","data"),
    Input({"type":"cl-card","index":dash.ALL},"n_clicks"),
    prevent_initial_call=True,
)
def select_classe(n_clicks):
    if not ctx.triggered_id or not isinstance(ctx.triggered_id, dict):
        return dash.no_update
    return ctx.triggered_id["index"]


@callback(
    Output("cl-detail","children"),
    Input("cl-selected","data"),
    Input("cl-refresh","data"),
)
def render_detail(cl_id, r):
    if not cl_id:
        return html.Div()
    db = SessionLocal()
    try:
        cl       = db.query(Classe).get(cl_id)
        if not cl: return html.Div()
        students = db.query(Student).filter_by(classe_id=cl_id, actif=True)\
                     .order_by(Student.nom).all()
        cc_links = db.query(CoursClasse).filter_by(classe_id=cl_id).all()
        courses  = db.query(Course).all()
        cours_map = {c.code: c for c in courses}

        # Dropdown pour affecter cours
        cours_opts = [{"label":f"{c.code} — {c.libelle}","value":c.code}
                      for c in courses]

        return html.Div([
            html.Div([
                html.Div([
                    html.Div(cl.nom, style={"fontFamily":"Times New Roman,serif",
                             "fontSize":"24px","fontWeight":"700","marginBottom":"4px"}),
                    html.Div(f"{cl.code} — {cl.filiere or ''} — {cl.annee or ''}",
                             style={"fontSize":"12px","color":"var(--muted)","letterSpacing":"1px"}),
                ], style={"flex":"1"}),
                html.Button("Fermer", id="btn-cl-fermer", n_clicks=0, className="btn-sga"),
            ], style={"display":"flex","alignItems":"center","marginBottom":"20px"}),

            html.Div([
                # Etudiants
                html.Div([
                    html.Div(f"Etudiants ({len(students)})", className="sga-card-title",
                             style={"marginBottom":"12px"}),
                    html.Div([
                        html.Div("Affecter un etudiant", className="sga-label"),
                        html.Div([
                            dcc.Dropdown(id="cl-add-etu", placeholder="Selectionner...",
                                         style={"flex":"1"}),
                            html.Button("Affecter", id="btn-cl-add-etu", n_clicks=0,
                                        className="btn-sga btn-gold", style={"flexShrink":"0"}),
                        ], style={"display":"flex","gap":"8px","marginBottom":"12px"}),
                        html.Div(id="cl-etu-feedback"),
                    ]),
                    html.Div([
                        html.Div([
                            html.Div(f"{s.nom} {s.prenom}",
                                     style={"fontWeight":"600","fontSize":"13px"}),
                            html.Div(s.email or "",
                                     style={"fontSize":"11px","color":"var(--muted)"}),
                        ], style={"padding":"10px 0","borderBottom":"1px solid var(--border)"})
                        for s in students
                    ] if students else [html.Div("Aucun etudiant.",
                                                 style={"color":"var(--muted)","padding":"16px",
                                                        "textAlign":"center"})]),
                ], className="sga-card", style={"flex":"1"}),

                # Cours
                html.Div([
                    html.Div(f"Cours ({len(cc_links)})", className="sga-card-title",
                             style={"marginBottom":"12px"}),
                    html.Div([
                        html.Div("Ajouter un cours", className="sga-label"),
                        html.Div([
                            dcc.Dropdown(id="cl-add-cours", options=cours_opts,
                                         placeholder="Selectionner...", style={"flex":"1"}),
                            html.Button("Ajouter", id="btn-cl-add-cours", n_clicks=0,
                                        className="btn-sga btn-gold", style={"flexShrink":"0"}),
                        ], style={"display":"flex","gap":"8px","marginBottom":"12px"}),
                        html.Div(id="cl-cours-feedback"),
                    ]),
                    html.Div([
                        html.Div([
                            html.Span(cc.course_code, style={"fontFamily":"JetBrains Mono,monospace",
                                      "fontWeight":"700","fontSize":"11px","color":"var(--gold)",
                                      "marginRight":"10px"}),
                            html.Span(cours_map[cc.course_code].libelle
                                      if cc.course_code in cours_map else "—",
                                      style={"fontSize":"13px"}),
                        ], style={"padding":"10px 0","borderBottom":"1px solid var(--border)"})
                        for cc in cc_links
                    ] if cc_links else [html.Div("Aucun cours.",
                                                  style={"color":"var(--muted)","padding":"16px",
                                                         "textAlign":"center"})]),
                ], className="sga-card", style={"flex":"1"}),
            ], style={"display":"flex","gap":"20px"}),

            # Store pour passer cl_id aux callbacks
            dcc.Store(id="cl-detail-id", data=cl_id),
        ], className="sga-card")
    finally:
        db.close()


@callback(
    Output("cl-add-etu","options"),
    Input("cl-detail-id","data"),
    Input("cl-refresh","data"),
)
def load_etu_sans_classe(cl_id, r):
    db = SessionLocal()
    try:
        sans_classe = db.query(Student).filter(
            Student.actif == True,
            Student.classe_id == None
        ).order_by(Student.nom).all()
        return [{"label":f"{s.nom} {s.prenom}","value":s.id} for s in sans_classe]
    finally:
        db.close()


@callback(
    Output("cl-etu-feedback","children"),
    Output("cl-refresh","data", allow_duplicate=True),
    Input("btn-cl-add-etu","n_clicks"),
    State("cl-add-etu","value"),
    State("cl-detail-id","data"),
    State("cl-refresh","data"),
    prevent_initial_call=True,
)
def affecter_etudiant(n, stu_id, cl_id, refresh):
    if not stu_id or not cl_id:
        return dash.no_update, dash.no_update
    db = SessionLocal()
    try:
        stu = db.query(Student).get(stu_id)
        if stu:
            stu.classe_id = cl_id
            db.commit()
            return html.Div(f"{stu.prenom} {stu.nom} affecte.",
                            className="sga-alert sga-alert-success"), (refresh or 0)+1
        return dash.no_update, dash.no_update
    finally:
        db.close()


@callback(
    Output("cl-cours-feedback","children"),
    Output("cl-refresh","data", allow_duplicate=True),
    Input("btn-cl-add-cours","n_clicks"),
    State("cl-add-cours","value"),
    State("cl-detail-id","data"),
    State("cl-refresh","data"),
    prevent_initial_call=True,
)
def ajouter_cours(n, course_code, cl_id, refresh):
    if not course_code or not cl_id:
        return dash.no_update, dash.no_update
    db = SessionLocal()
    try:
        existing = db.query(CoursClasse).filter_by(
            course_code=course_code, classe_id=cl_id).first()
        if existing:
            return html.Div("Ce cours est deja dans cette classe.",
                            className="sga-alert sga-alert-warning"), dash.no_update
        cc = CoursClasse()
        cc.course_code = course_code
        cc.classe_id   = cl_id
        cc.created_at  = datetime.now()
        db.add(cc); db.commit()
        return html.Div("Cours ajoute.", className="sga-alert sga-alert-success"), (refresh or 0)+1
    except Exception as e:
        db.rollback()
        return html.Div(str(e), className="sga-alert sga-alert-danger"), dash.no_update
    finally:
        db.close()


@callback(
    Output("cl-selected","data", allow_duplicate=True),
    Input("btn-cl-fermer","n_clicks"),
    prevent_initial_call=True,
)
def fermer_detail(n):
    return None
