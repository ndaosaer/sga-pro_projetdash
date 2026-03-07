import dash, json
from dash import html, dcc, Input, Output, State, callback, ctx
from database import SessionLocal
from models import Concours, Candidat, Communique, Student, User
from werkzeug.security import generate_password_hash
from datetime import datetime, date

dash.register_page(__name__, path="/admin-concours", name="Concours Admin")

STATUT_COLORS = {
    "en_attente":       ("var(--muted)",    "En attente"),
    "dossier_incomplet":("var(--copper)",   "Dossier incomplet"),
    "dossier_complet":  ("#2D6A3F",         "Dossier complet"),
    "valide":           ("var(--gold)",     "Valide"),
    "rejete":           ("var(--red)",      "Rejete"),
    "admis":            ("var(--gold)",     "Admis"),
}
PAY_COLORS = {
    "non_paye": ("var(--red)",    "Non paye"),
    "paye":     ("var(--green)",  "Paye"),
    "simule":   ("var(--copper)", "Simule"),
}

def layout():
    return html.Div([
        dcc.Store(id="ac-refresh", data=0),
        dcc.Store(id="ac-selected", data=None),

        html.Div([
            html.Div([
                html.Div("Gestion des Concours", className="page-title"),
                html.Div("Administration des candidatures et admissions", className="page-subtitle"),
            ]),
            html.Button("+ Nouveau concours", id="btn-ac-new-concours",
                        n_clicks=0, className="btn-sga btn-gold"),
        ], className="topbar"),

        html.Div([
            # Onglets
            html.Div([
                html.Button("Tableau de bord",  id="ac-tab-dash",  n_clicks=0, className="btn-sga btn-gold"),
                html.Button("Candidats",         id="ac-tab-cand",  n_clicks=0, className="btn-sga"),
                html.Button("Communiques",       id="ac-tab-comm",  n_clicks=0, className="btn-sga"),
                html.Button("Admissions",        id="ac-tab-adm",   n_clicks=0, className="btn-sga"),
            ], style={"display":"flex","gap":"8px","marginBottom":"24px"}),

            html.Div(id="ac-content"),
        ], style={"padding":"24px"}),

        # Modal nouveau concours
        html.Div([
            html.Div([
                html.Div("Creer un nouveau concours", className="sga-card-title",
                         style={"marginBottom":"20px"}),
                html.Div("Nom du concours", className="sga-label"),
                dcc.Input(id="nc-nom", placeholder="ex: Concours ENSAE 2026",
                          className="sga-input", style={"width":"100%","marginBottom":"12px"}),
                html.Div([
                    html.Div([
                        html.Div("Annee", className="sga-label"),
                        dcc.Input(id="nc-annee", placeholder="2026", type="number",
                                  className="sga-input", style={"width":"100%"}),
                    ], style={"flex":"1"}),
                    html.Div([
                        html.Div("Frais de dossier (FCFA)", className="sga-label"),
                        dcc.Input(id="nc-frais", placeholder="15000", type="number",
                                  className="sga-input", style={"width":"100%"}),
                    ], style={"flex":"1"}),
                ], style={"display":"flex","gap":"16px","marginBottom":"12px"}),
                html.Div([
                    html.Div([
                        html.Div("Ouverture inscriptions", className="sga-label"),
                        dcc.Input(id="nc-ouverture", type="date", className="sga-input", style={"width":"100%"}),
                    ], style={"flex":"1"}),
                    html.Div([
                        html.Div("Cloture inscriptions", className="sga-label"),
                        dcc.Input(id="nc-cloture", type="date", className="sga-input", style={"width":"100%"}),
                    ], style={"flex":"1"}),
                ], style={"display":"flex","gap":"16px","marginBottom":"12px"}),
                html.Div([
                    html.Div([
                        html.Div("Date du concours", className="sga-label"),
                        dcc.Input(id="nc-epreuve", type="date", className="sga-input", style={"width":"100%"}),
                    ], style={"flex":"1"}),
                    html.Div([
                        html.Div("Date des resultats", className="sga-label"),
                        dcc.Input(id="nc-resultats", type="date", className="sga-input", style={"width":"100%"}),
                    ], style={"flex":"1"}),
                ], style={"display":"flex","gap":"16px","marginBottom":"12px"}),
                html.Div("Description", className="sga-label"),
                dcc.Textarea(id="nc-desc", placeholder="Description du concours...",
                             style={"width":"100%","minHeight":"80px","marginBottom":"20px",
                                    "background":"var(--bg-primary)","border":"1px solid var(--border)",
                                    "borderRadius":"4px","padding":"10px","color":"var(--text-primary)",
                                    "fontFamily":"JetBrains Mono,monospace","fontSize":"13px",
                                    "resize":"vertical"}),
                html.Div([
                    html.Button("Creer le concours", id="btn-nc-save", n_clicks=0,
                                className="btn-sga btn-gold"),
                    html.Button("Annuler", id="btn-nc-cancel", n_clicks=0, className="btn-sga"),
                ], style={"display":"flex","gap":"10px"}),
                html.Div(id="nc-feedback", style={"marginTop":"12px"}),
            ], style={"background":"var(--bg-card)","border":"1px solid var(--border)",
                      "borderRadius":"6px","padding":"32px","maxWidth":"640px",
                      "margin":"0 auto","position":"relative","zIndex":"10"}),
        ], id="modal-nc", style={"display":"none","position":"fixed","inset":"0",
                                  "background":"rgba(0,0,0,0.5)","zIndex":"999",
                                  "alignItems":"center","justifyContent":"center"}),
    ])


# ── Afficher/cacher le modal ──
@callback(
    Output("modal-nc","style"),
    Input("btn-ac-new-concours","n_clicks"),
    Input("btn-nc-cancel","n_clicks"),
    Input("btn-nc-save","n_clicks"),
    prevent_initial_call=True,
)
def toggle_modal(n_new, n_cancel, n_save):
    show = {"display":"flex","position":"fixed","inset":"0",
            "background":"rgba(0,0,0,0.5)","zIndex":"999",
            "alignItems":"center","justifyContent":"center"}
    hide = {"display":"none"}
    if ctx.triggered_id == "btn-ac-new-concours":
        return show
    return hide


# ── Sauvegarder nouveau concours ──
@callback(
    Output("nc-feedback","children"),
    Output("ac-refresh","data"),
    Input("btn-nc-save","n_clicks"),
    State("nc-nom","value"),
    State("nc-annee","value"),
    State("nc-frais","value"),
    State("nc-ouverture","value"),
    State("nc-cloture","value"),
    State("nc-epreuve","value"),
    State("nc-resultats","value"),
    State("nc-desc","value"),
    State("ac-refresh","data"),
    prevent_initial_call=True,
)
def creer_concours(n, nom, annee, frais, ouverture, cloture, epreuve, resultats, desc, refresh):
    if not nom or not annee:
        return html.Div("Nom et annee requis.", className="sga-alert sga-alert-warning"), dash.no_update
    db = SessionLocal()
    try:
        def parse_date(s):
            return datetime.strptime(s, "%Y-%m-%d").date() if s else None
        c = Concours()
        c.nom            = nom
        c.annee          = int(annee)
        c.frais_dossier  = float(frais or 0)
        c.date_ouverture = parse_date(ouverture)
        c.date_cloture   = parse_date(cloture)
        c.date_epreuve   = parse_date(epreuve)
        c.date_resultats = parse_date(resultats)
        c.description    = desc or ""
        c.actif          = True
        c.created_at     = datetime.now()
        db.add(c); db.commit()
        return html.Div("Concours cree.", className="sga-alert sga-alert-success"), (refresh or 0)+1
    except Exception as e:
        db.rollback()
        return html.Div(str(e), className="sga-alert sga-alert-danger"), dash.no_update
    finally:
        db.close()


# ── Contenu principal selon onglet ──
@callback(
    Output("ac-content","children"),
    Input("ac-tab-dash","n_clicks"),
    Input("ac-tab-cand","n_clicks"),
    Input("ac-tab-comm","n_clicks"),
    Input("ac-tab-adm","n_clicks"),
    Input("ac-refresh","data"),
)
def render_tab(n_dash, n_cand, n_comm, n_adm, refresh):
    tab = "dash"
    if ctx.triggered_id == "ac-tab-cand": tab = "cand"
    elif ctx.triggered_id == "ac-tab-comm": tab = "comm"
    elif ctx.triggered_id == "ac-tab-adm": tab = "adm"

    db = SessionLocal()
    try:
        concours_list = db.query(Concours).order_by(Concours.annee.desc()).all()
        if not concours_list:
            return html.Div([
                html.Div("Aucun concours cree.", style={"textAlign":"center","color":"var(--muted)",
                          "padding":"60px","fontSize":"16px"}),
                html.Div("Cliquez sur + Nouveau concours pour commencer.",
                         style={"textAlign":"center","color":"var(--muted)","fontSize":"13px"}),
            ])
        c = concours_list[0]  # concours actif = le plus recent
        candidats = db.query(Candidat).filter_by(concours_id=c.id).all()

        if tab == "dash":
            return _render_dashboard(c, candidats, concours_list)
        elif tab == "cand":
            return _render_candidats(c, candidats, concours_list)
        elif tab == "comm":
            comms = db.query(Communique).filter_by(concours_id=c.id).order_by(Communique.created_at.desc()).all()
            return _render_communiques(c, comms, concours_list)
        elif tab == "adm":
            return _render_admissions(c, candidats, concours_list)
    finally:
        db.close()


def _concours_selector(concours_list, current_id):
    return html.Div([
        html.Span("Concours :", style={"fontSize":"11px","letterSpacing":"2px",
                  "textTransform":"uppercase","color":"var(--muted)","marginRight":"8px"}),
        dcc.Dropdown(
            options=[{"label":f"{c.nom} ({c.annee})","value":c.id} for c in concours_list],
            value=current_id, clearable=False, style={"minWidth":"280px"},
            id="ac-concours-selector",
        ),
    ], style={"display":"flex","alignItems":"center","marginBottom":"20px"})


def _render_dashboard(c, candidats, concours_list):
    total    = len(candidats)
    complets = sum(1 for x in candidats if x.statut in ("dossier_complet","valide","admis"))
    payes    = sum(1 for x in candidats if x.paiement_statut in ("paye","simule"))
    admis    = sum(1 for x in candidats if x.admis)

    def fmt_date(d): return d.strftime("%d/%m/%Y") if d else "—"

    return html.Div([
        _concours_selector(concours_list, c.id),

        # KPIs
        html.Div([
            _kpi(str(total),    "Candidats inscrits",  "var(--gold)"),
            _kpi(str(complets), "Dossiers complets",    "var(--green)"),
            _kpi(str(payes),    "Paiements recus",      "var(--copper)"),
            _kpi(str(admis),    "Admis",                "var(--gold)"),
        ], style={"display":"grid","gridTemplateColumns":"repeat(4,1fr)","gap":"16px","marginBottom":"24px"}),

        # Info concours
        html.Div([
            html.Div("Informations du concours", className="sga-card-title",
                     style={"marginBottom":"16px"}),
            html.Div([
                _info_row("Nom",                c.nom),
                _info_row("Annee",              str(c.annee)),
                _info_row("Frais de dossier",   f"{c.frais_dossier:,.0f} FCFA"),
                _info_row("Ouverture",          fmt_date(c.date_ouverture)),
                _info_row("Cloture",            fmt_date(c.date_cloture)),
                _info_row("Date du concours",   fmt_date(c.date_epreuve)),
                _info_row("Publication resultats", fmt_date(c.date_resultats)),
            ]),
        ], className="sga-card", style={"marginBottom":"20px"}),

        # Repartition statuts
        html.Div([
            html.Div("Repartition des dossiers", className="sga-card-title",
                     style={"marginBottom":"16px"}),
            *[html.Div([
                html.Div([
                    html.Span(label, style={"fontSize":"13px","color":"var(--text-primary)"}),
                ]),
                html.Div([
                    html.Div(style={
                        "height":"8px","borderRadius":"4px","background":color,
                        "width":f"{(sum(1 for x in candidats if x.statut==key)/total*100 if total else 0):.0f}%",
                        "minWidth":"4px","transition":"width 0.5s",
                    }),
                    html.Span(str(sum(1 for x in candidats if x.statut==key)),
                              style={"fontSize":"12px","color":color,"fontWeight":"700",
                                     "marginLeft":"8px","fontFamily":"JetBrains Mono,monospace"}),
                ], style={"display":"flex","alignItems":"center","gap":"8px","flex":"1"}),
            ], style={"display":"flex","alignItems":"center","gap":"16px","padding":"8px 0",
                      "borderBottom":"1px solid var(--border)"})
              for key, (color, label) in STATUT_COLORS.items()],
        ], className="sga-card"),
    ])


def _render_candidats(c, candidats, concours_list):
    rows = []
    for i, cand in enumerate(sorted(candidats, key=lambda x: x.created_at or datetime.min, reverse=True)):
        col, lbl = STATUT_COLORS.get(cand.statut, ("var(--muted)","—"))
        pcol, plbl = PAY_COLORS.get(cand.paiement_statut, ("var(--muted)","—"))
        rows.append(html.Tr([
            html.Td(cand.numero_candidat or f"#{cand.id:04d}",
                    style={"fontFamily":"JetBrains Mono,monospace","fontWeight":"700",
                           "color":"var(--gold)","fontSize":"12px"}),
            html.Td(f"{cand.nom} {cand.prenom}", style={"fontWeight":"600"}),
            html.Td(cand.email, style={"fontSize":"12px","color":"var(--muted)"}),
            html.Td(html.Span(lbl, style={"color":col,"fontWeight":"600","fontSize":"11px"})),
            html.Td(html.Span(plbl, style={"color":pcol,"fontWeight":"600","fontSize":"11px"})),
            html.Td([
                html.Button("Valider", id={"type":"btn-valider","index":cand.id},
                            n_clicks=0,
                            style={"fontSize":"9px","padding":"4px 10px","marginRight":"4px",
                                   "background":"rgba(45,106,63,0.1)","border":"1px solid var(--green)",
                                   "borderRadius":"3px","color":"var(--green)","cursor":"pointer"}),
                html.Button("Rejeter", id={"type":"btn-rejeter","index":cand.id},
                            n_clicks=0,
                            style={"fontSize":"9px","padding":"4px 10px",
                                   "background":"rgba(139,37,0,0.1)","border":"1px solid var(--red)",
                                   "borderRadius":"3px","color":"var(--red)","cursor":"pointer"}),
            ]),
        ]))

    return html.Div([
        _concours_selector(concours_list, c.id),
        html.Div([
            html.Div(f"{len(candidats)} candidats — {c.nom} {c.annee}",
                     className="sga-card-title", style={"marginBottom":"16px"}),
            html.Table([
                html.Thead(html.Tr([
                    html.Th("N° Candidat"), html.Th("Nom & Prenom"),
                    html.Th("Email"), html.Th("Statut dossier"),
                    html.Th("Paiement"), html.Th("Actions"),
                ])),
                html.Tbody(rows),
            ], className="sga-table", style={"width":"100%"})
            if rows else html.Div("Aucun candidat inscrit.",
                                  style={"textAlign":"center","color":"var(--muted)","padding":"40px"}),
        ], className="sga-card"),
        html.Div(id="ac-cand-feedback", style={"marginTop":"12px"}),
    ])



def _comm_items(comms, TYPE_COLORS):
    if not comms:
        return [html.Div("Aucun communique.", style={"color":"var(--muted)","textAlign":"center","padding":"40px"})]
    items = []
    for comm in comms:
        col = TYPE_COLORS.get(comm.type_comm, "var(--gold)")
        items.append(html.Div([
            html.Div([
                html.Span(comm.type_comm.upper(),
                          style={"fontSize":"9px","letterSpacing":"2px","color":col,
                                 "fontWeight":"700","marginRight":"12px",
                                 "border":f"1px solid {col}",
                                 "padding":"2px 8px","borderRadius":"2px"}),
                html.Span(comm.titre, style={"fontWeight":"700","fontSize":"15px"}),
            ], style={"display":"flex","alignItems":"center","marginBottom":"8px"}),
            html.Div(comm.contenu, style={"fontSize":"13px","color":"var(--muted)",
                                          "lineHeight":"1.7","marginBottom":"8px"}),
            html.Div(comm.created_at.strftime("%d/%m/%Y %H:%M") if comm.created_at else "",
                     style={"fontSize":"10px","color":"var(--muted)"}),
        ], style={"padding":"16px","background":"var(--bg-secondary)","borderRadius":"4px",
                  "marginBottom":"8px","borderLeft":f"3px solid {col}"}))
    return items

def _render_communiques(c, comms, concours_list):
    TYPE_COLORS = {"info":"var(--gold)","urgent":"var(--red)","resultat":"var(--green)"}
    return html.Div([
        _concours_selector(concours_list, c.id),

        # Formulaire
        html.Div([
            html.Div("Publier un communique", className="sga-card-title",
                     style={"marginBottom":"16px"}),
            html.Div([
                html.Div([
                    html.Div("Type", className="sga-label"),
                    dcc.Dropdown(id="comm-type",
                                 options=[{"label":"Information","value":"info"},
                                          {"label":"Urgent","value":"urgent"},
                                          {"label":"Resultats","value":"resultat"}],
                                 value="info", clearable=False),
                ], style={"flex":"1"}),
                html.Div([
                    html.Div("Titre", className="sga-label"),
                    dcc.Input(id="comm-titre", placeholder="Titre du communique",
                              className="sga-input", style={"width":"100%"}),
                ], style={"flex":"3"}),
            ], style={"display":"flex","gap":"16px","marginBottom":"12px"}),
            dcc.Textarea(id="comm-contenu", placeholder="Contenu du communique...",
                         style={"width":"100%","minHeight":"100px","marginBottom":"12px",
                                "background":"var(--bg-primary)","border":"1px solid var(--border)",
                                "borderRadius":"4px","padding":"10px","color":"var(--text-primary)",
                                "fontFamily":"JetBrains Mono,monospace","fontSize":"13px","resize":"vertical"}),
            html.Button("Publier", id="btn-comm-publier", n_clicks=0, className="btn-sga btn-gold"),
            html.Div(id="comm-feedback", style={"marginTop":"12px"}),
        ], className="sga-card", style={"marginBottom":"20px"}),

        # Liste
        html.Div([
            html.Div("Communiques publies", className="sga-card-title",
                     style={"marginBottom":"16px"}),
            *(_comm_items(comms, TYPE_COLORS)),
        ], className="sga-card"),
    ])


def _render_admissions(c, candidats, concours_list):
    eligible = [x for x in candidats if x.statut == "valide" and not x.admis]
    admis    = [x for x in candidats if x.admis]

    def card(cand, action=True):
        return html.Div([
            html.Div([
                html.Div(f"{cand.prenom} {cand.nom}",
                         style={"fontWeight":"700","fontSize":"15px","marginBottom":"2px"}),
                html.Div(cand.email, style={"fontSize":"12px","color":"var(--muted)"}),
                html.Div(cand.niveau_etudes or "—",
                         style={"fontSize":"11px","color":"var(--muted)","marginTop":"4px"}),
            ], style={"flex":"1"}),
            html.Div([
                html.Button("Admettre + Creer compte etudiant",
                            id={"type":"btn-admettre","index":cand.id},
                            n_clicks=0, className="btn-sga btn-gold",
                            style={"fontSize":"10px","padding":"8px 14px"})
                if action else
                html.Span("Admis", style={"color":"var(--green)","fontWeight":"700","fontSize":"13px"}),
            ]),
        ], style={"display":"flex","alignItems":"center","gap":"16px","padding":"16px",
                  "background":"var(--bg-secondary)","borderRadius":"4px","marginBottom":"8px"})

    return html.Div([
        _concours_selector(concours_list, c.id),
        html.Div([
            html.Div(f"{len(eligible)} candidats eligibles a l'admission",
                     className="sga-card-title", style={"marginBottom":"16px"}),
            *(([card(x) for x in eligible]) if eligible else
              [html.Div("Aucun dossier valide en attente d'admission.",
                        style={"color":"var(--muted)","textAlign":"center","padding":"32px"})]),
            html.Div(id="ac-adm-feedback", style={"marginTop":"12px"}),
        ], className="sga-card", style={"marginBottom":"20px"}),

        html.Div([
            html.Div(f"{len(admis)} etudiants admis", className="sga-card-title",
                     style={"marginBottom":"16px"}),
            *(([card(x, action=False) for x in admis]) if admis else
              [html.Div("Aucun admis encore.", style={"color":"var(--muted)","textAlign":"center","padding":"24px"})]),
        ], className="sga-card"),
    ])


# ── Valider / Rejeter candidat ──
@callback(
    Output("ac-cand-feedback","children"),
    Output("ac-refresh","data", allow_duplicate=True),
    Input({"type":"btn-valider","index":dash.ALL},"n_clicks"),
    Input({"type":"btn-rejeter","index":dash.ALL},"n_clicks"),
    State("ac-refresh","data"),
    prevent_initial_call=True,
)
def changer_statut(n_val, n_rej, refresh):
    triggered = ctx.triggered_id
    if not triggered or not isinstance(triggered, dict):
        return dash.no_update, dash.no_update
    cand_id = triggered["index"]
    action  = triggered["type"]
    db = SessionLocal()
    try:
        cand = db.query(Candidat).get(cand_id)
        if not cand:
            return html.Div("Candidat introuvable.", className="sga-alert sga-alert-danger"), dash.no_update
        if action == "btn-valider":
            cand.statut = "valide"
            msg = f"Dossier de {cand.prenom} {cand.nom} valide."
            cls = "sga-alert sga-alert-success"
        else:
            cand.statut = "rejete"
            msg = f"Dossier de {cand.prenom} {cand.nom} rejete."
            cls = "sga-alert sga-alert-danger"
        db.commit()
        return html.Div(msg, className=cls), (refresh or 0)+1
    finally:
        db.close()


# ── Admettre + creer etudiant ──
@callback(
    Output("ac-adm-feedback","children"),
    Output("ac-refresh","data", allow_duplicate=True),
    Input({"type":"btn-admettre","index":dash.ALL},"n_clicks"),
    State("ac-refresh","data"),
    prevent_initial_call=True,
)
def admettre_candidat(n_clicks, refresh):
    triggered = ctx.triggered_id
    if not triggered or not isinstance(triggered, dict):
        return dash.no_update, dash.no_update
    cand_id = triggered["index"]
    db = SessionLocal()
    try:
        cand = db.query(Candidat).get(cand_id)
        if not cand:
            return html.Div("Candidat introuvable.", className="sga-alert sga-alert-danger"), dash.no_update

        # Creer l'etudiant
        stu = Student()
        stu.nom            = cand.nom
        stu.prenom         = cand.prenom
        stu.email          = cand.email
        stu.date_naissance = cand.date_naissance
        stu.actif          = True
        stu.created_at     = datetime.now()
        db.add(stu); db.flush()

        # Creer le compte utilisateur
        username = f"{cand.prenom.lower().replace(' ','')}.{cand.nom.lower().replace(' ','')}"
        password = f"sga{cand.id:04d}"
        u = User()
        u.username      = username
        u.password_hash = generate_password_hash(password)
        u.role          = "student"
        u.linked_id     = stu.id
        u.created_at    = datetime.now()
        db.add(u)

        # Mettre a jour le candidat
        cand.admis      = True
        cand.statut     = "admis"
        cand.student_id = stu.id
        db.commit()

        return html.Div([
            html.Div(f"{cand.prenom} {cand.nom} admis et compte etudiant cree.",
                     className="sga-alert sga-alert-success"),
            html.Div(f"Identifiant : {username}  |  Mot de passe temporaire : {password}",
                     style={"fontFamily":"JetBrains Mono,monospace","fontSize":"13px",
                            "padding":"10px","background":"var(--bg-secondary)",
                            "borderRadius":"4px","marginTop":"8px","color":"var(--gold)"}),
        ]), (refresh or 0)+1
    except Exception as e:
        db.rollback()
        return html.Div(str(e), className="sga-alert sga-alert-danger"), dash.no_update
    finally:
        db.close()


# ── Publier un communique ──
@callback(
    Output("comm-feedback","children"),
    Output("ac-refresh","data", allow_duplicate=True),
    Input("btn-comm-publier","n_clicks"),
    State("comm-titre","value"),
    State("comm-contenu","value"),
    State("comm-type","value"),
    State("ac-refresh","data"),
    prevent_initial_call=True,
)
def publier_communique(n, titre, contenu, type_comm, refresh):
    if not titre or not contenu:
        return html.Div("Titre et contenu requis.", className="sga-alert sga-alert-warning"), dash.no_update
    db = SessionLocal()
    try:
        concours = db.query(Concours).order_by(Concours.annee.desc()).first()
        if not concours:
            return html.Div("Aucun concours actif.", className="sga-alert sga-alert-danger"), dash.no_update
        comm = Communique()
        comm.concours_id = concours.id
        comm.titre       = titre
        comm.contenu     = contenu
        comm.type_comm   = type_comm or "info"
        comm.publie      = True
        comm.created_at  = datetime.now()
        db.add(comm); db.commit()
        return html.Div("Communique publie.", className="sga-alert sga-alert-success"), (refresh or 0)+1
    except Exception as e:
        db.rollback()
        return html.Div(str(e), className="sga-alert sga-alert-danger"), dash.no_update
    finally:
        db.close()


def _kpi(val, label, color):
    return html.Div([
        html.Div(val, className="kpi-value", style={"color":color,"fontSize":"36px"}),
        html.Div(label, className="kpi-label"),
    ], className="kpi-card")

def _info_row(label, val):
    return html.Div([
        html.Div(label, style={"fontSize":"11px","letterSpacing":"1px","color":"var(--muted)",
                               "textTransform":"uppercase","minWidth":"180px"}),
        html.Div(val,   style={"fontSize":"14px","fontWeight":"600","color":"var(--text-primary)"}),
    ], style={"display":"flex","alignItems":"center","padding":"8px 0",
              "borderBottom":"1px solid var(--border)"})
