import dash
from dash import html, dcc, Input, Output, State, callback, ctx
from database import SessionLocal
from models import Student, FraisScolarite, Paiement
from datetime import datetime, date

dash.register_page(__name__, path="/paiements", name="Paiements")

ANNEE_COURANTE = "2025-2026"
MODES = ["Especes", "Wave", "Orange Money", "Virement", "Carte"]
MODE_COLORS = {
    "Especes":      "var(--muted)",
    "Wave":         "#1B74E4",
    "Orange Money": "#FF6600",
    "Virement":     "var(--green)",
    "Carte":        "var(--copper)",
}


def layout():
    return html.Div([
        dcc.Store(id="pay-refresh", data=0),
        dcc.Store(id="pay-selected-student", data=None),

        html.Div([
            html.Div([
                html.Div("Paiements Scolarite", className="page-title"),
                html.Div("Suivi des frais et des versements", className="page-subtitle"),
            ]),
            html.Div([
                html.Button("+ Configurer les frais",  id="btn-pay-config",
                            n_clicks=0, className="btn-sga"),
                html.Button("+ Enregistrer un paiement", id="btn-pay-new",
                            n_clicks=0, className="btn-sga btn-gold"),
            ], style={"display":"flex","gap":"8px"}),
        ], className="topbar"),

        html.Div([
            # Onglets
            html.Div([
                html.Button("Vue globale",    id="pay-tab-global", n_clicks=0, className="btn-sga btn-gold"),
                html.Button("Par etudiant",   id="pay-tab-etu",    n_clicks=0, className="btn-sga"),
                html.Button("Relances",       id="pay-tab-relance",n_clicks=0, className="btn-sga"),
            ], style={"display":"flex","gap":"8px","marginBottom":"24px"}),

            html.Div(id="pay-content"),
        ], style={"padding":"24px"}),

        # ── Panneau inline : configurer frais ──
        html.Div([
            html.Div([
                html.Div([
                    html.Div("Configurer les frais de scolarite", className="sga-card-title"),
                    html.Button("Fermer", id="btn-cfg-cancel", n_clicks=0,
                                style={"background":"none","border":"none","fontSize":"20px",
                                       "cursor":"pointer","color":"var(--muted)","lineHeight":"1"}),
                ], style={"display":"flex","justifyContent":"space-between",
                          "alignItems":"center","marginBottom":"20px"}),
                html.Div("Etudiant", className="sga-label"),
                dcc.Dropdown(id="cfg-student", placeholder="Selectionner un etudiant...",
                             style={"marginBottom":"14px"}),
                html.Div([
                    html.Div([
                        html.Div("Annee academique", className="sga-label"),
                        dcc.Input(id="cfg-annee", value=ANNEE_COURANTE,
                                  className="sga-input", style={"width":"100%"}),
                    ], style={"flex":"1"}),
                    html.Div([
                        html.Div("Montant total (FCFA)", className="sga-label"),
                        dcc.Input(id="cfg-montant", type="number", placeholder="500000",
                                  className="sga-input", style={"width":"100%"}),
                    ], style={"flex":"1"}),
                    html.Div([
                        html.Div("Nb de tranches", className="sga-label"),
                        dcc.Input(id="cfg-echeances", type="number", value=3, min=1, max=12,
                                  className="sga-input", style={"width":"100%"}),
                    ], style={"flex":"1"}),
                ], style={"display":"flex","gap":"16px","marginBottom":"20px"}),
                html.Div([
                    html.Button("Enregistrer", id="btn-cfg-save", n_clicks=0, className="btn-sga btn-gold"),
                ], style={"display":"flex","gap":"10px"}),
                html.Div(id="cfg-feedback", style={"marginTop":"12px"}),
            ], className="sga-card",
               style={"borderTop":"3px solid var(--em)","marginBottom":"24px"}),
        ], id="modal-cfg", style={"display":"none"}),

        # ── Panneau inline : enregistrer un paiement ──
        html.Div([
            html.Div([
                html.Div([
                    html.Div("Enregistrer un paiement", className="sga-card-title"),
                    html.Button("Fermer", id="btn-np-cancel", n_clicks=0,
                                style={"background":"none","border":"none","fontSize":"20px",
                                       "cursor":"pointer","color":"var(--muted)","lineHeight":"1"}),
                ], style={"display":"flex","justifyContent":"space-between",
                          "alignItems":"center","marginBottom":"20px"}),
                html.Div("Etudiant", className="sga-label"),
                dcc.Dropdown(id="np-student", placeholder="Selectionner un etudiant...",
                             style={"marginBottom":"14px"}),
                html.Div([
                    html.Div([
                        html.Div("Montant (FCFA)", className="sga-label"),
                        dcc.Input(id="np-montant", type="number", placeholder="150000",
                                  className="sga-input", style={"width":"100%"}),
                    ], style={"flex":"1"}),
                    html.Div([
                        html.Div("Date", className="sga-label"),
                        dcc.Input(id="np-date", type="date",
                                  value=date.today().isoformat(),
                                  className="sga-input", style={"width":"100%"}),
                    ], style={"flex":"1"}),
                ], style={"display":"flex","gap":"16px","marginBottom":"14px"}),
                html.Div([
                    html.Div([
                        html.Div("Mode de paiement", className="sga-label"),
                        dcc.Dropdown(id="np-mode",
                                     options=[{"label":m,"value":m} for m in MODES],
                                     value="Especes", clearable=False),
                    ], style={"flex":"1"}),
                    html.Div([
                        html.Div("Reference / Recu", className="sga-label"),
                        dcc.Input(id="np-ref", placeholder="N° recu ou reference",
                                  className="sga-input", style={"width":"100%"}),
                    ], style={"flex":"1"}),
                ], style={"display":"flex","gap":"16px","marginBottom":"14px"}),
                html.Div([
                    html.Div("Tranche N°", className="sga-label"),
                    dcc.Input(id="np-tranche", type="number", value=1, min=1,
                              className="sga-input", style={"width":"120px","marginBottom":"20px"}),
                ]),
                html.Div([
                    html.Button("Enregistrer", id="btn-np-save", n_clicks=0, className="btn-sga btn-gold"),
                ], style={"display":"flex","gap":"10px"}),
                html.Div(id="np-feedback", style={"marginTop":"12px"}),
            ], className="sga-card",
               style={"borderTop":"3px solid var(--gold)","marginBottom":"24px"}),
        ], id="modal-np", style={"display":"none"}),
    ])


# ── Charger la liste des etudiants dans les dropdowns ──
@callback(
    Output("cfg-student","options"),
    Output("np-student","options"),
    Input("pay-refresh","data"),
)
def load_students(refresh):
    db = SessionLocal()
    try:
        students = db.query(Student).filter_by(actif=True).order_by(Student.nom).all()
        opts = [{"label":f"{s.nom} {s.prenom}","value":s.id} for s in students]
        return opts, opts
    finally:
        db.close()


# ── Toggles modaux ──
@callback(
    Output("modal-cfg","style"),
    Input("btn-pay-config","n_clicks"),
    Input("btn-cfg-cancel","n_clicks"),
    Input("btn-cfg-save","n_clicks"),
    prevent_initial_call=True,
)
def toggle_cfg(n1, n2, n3):
    if ctx.triggered_id == "btn-pay-config":
        return {"display":"block"}
    return {"display":"none"}


@callback(
    Output("modal-np","style"),
    Input("btn-pay-new","n_clicks"),
    Input("btn-np-cancel","n_clicks"),
    Input("btn-np-save","n_clicks"),
    prevent_initial_call=True,
)
def toggle_np(n1, n2, n3):
    if ctx.triggered_id == "btn-pay-new":
        return {"display":"block"}
    return {"display":"none"}


# ── Sauvegarder config frais ──
@callback(
    Output("cfg-feedback","children"),
    Output("pay-refresh","data", allow_duplicate=True),
    Input("btn-cfg-save","n_clicks"),
    State("cfg-student","value"),
    State("cfg-annee","value"),
    State("cfg-montant","value"),
    State("cfg-echeances","value"),
    State("pay-refresh","data"),
    prevent_initial_call=True,
)
def sauver_config(n, student_id, annee, montant, echeances, refresh):
    if not student_id or not montant:
        return html.Div("Etudiant et montant requis.",
                        className="sga-alert sga-alert-warning"), dash.no_update
    db = SessionLocal()
    try:
        existing = db.query(FraisScolarite).filter_by(
            student_id=student_id, annee=annee or ANNEE_COURANTE).first()
        if existing:
            existing.montant_total = float(montant)
            existing.echeances     = int(echeances or 1)
        else:
            f = FraisScolarite()
            f.student_id    = student_id
            f.annee         = annee or ANNEE_COURANTE
            f.montant_total = float(montant)
            f.echeances     = int(echeances or 1)
            f.created_at    = datetime.now()
            db.add(f)
        db.commit()
        return html.Div("Frais enregistres.", className="sga-alert sga-alert-success"), (refresh or 0)+1
    except Exception as e:
        db.rollback()
        return html.Div(str(e), className="sga-alert sga-alert-danger"), dash.no_update
    finally:
        db.close()


# ── Enregistrer un paiement ──
@callback(
    Output("np-feedback","children"),
    Output("pay-refresh","data", allow_duplicate=True),
    Input("btn-np-save","n_clicks"),
    State("np-student","value"),
    State("np-montant","value"),
    State("np-date","value"),
    State("np-mode","value"),
    State("np-ref","value"),
    State("np-tranche","value"),
    State("pay-refresh","data"),
    prevent_initial_call=True,
)
def enregistrer_paiement(n, student_id, montant, date_str, mode, ref, tranche, refresh):
    if not student_id or not montant or not date_str:
        return html.Div("Etudiant, montant et date requis.",
                        className="sga-alert sga-alert-warning"), dash.no_update
    db = SessionLocal()
    try:
        # Trouver ou creer les frais
        frais = db.query(FraisScolarite).filter_by(
            student_id=student_id, annee=ANNEE_COURANTE).first()
        if not frais:
            frais = FraisScolarite()
            frais.student_id    = student_id
            frais.annee         = ANNEE_COURANTE
            frais.montant_total = float(montant)
            frais.echeances     = 1
            frais.created_at    = datetime.now()
            db.add(frais)
            db.flush()

        p = Paiement()
        p.frais_id      = frais.id
        p.student_id    = student_id
        p.montant       = float(montant)
        p.date_paiement = datetime.strptime(date_str, "%Y-%m-%d").date()
        p.mode          = mode or "Especes"
        p.reference     = ref
        p.tranche       = int(tranche or 1)
        p.valide        = True
        p.created_at    = datetime.now()
        db.add(p)
        db.commit()

        stu = db.query(Student).get(student_id)
        nom = f"{stu.nom} {stu.prenom}" if stu else str(student_id)
        return html.Div(f"Paiement de {float(montant):,.0f} FCFA enregistre pour {nom}.",
                        className="sga-alert sga-alert-success"), (refresh or 0)+1
    except Exception as e:
        db.rollback()
        return html.Div(str(e), className="sga-alert sga-alert-danger"), dash.no_update
    finally:
        db.close()


# ── Contenu selon onglet ──
@callback(
    Output("pay-content","children"),
    Input("pay-tab-global","n_clicks"),
    Input("pay-tab-etu","n_clicks"),
    Input("pay-tab-relance","n_clicks"),
    Input("pay-refresh","data"),
)
def render_tab(n_g, n_e, n_r, refresh):
    tab = "global"
    if ctx.triggered_id == "pay-tab-etu":     tab = "etu"
    elif ctx.triggered_id == "pay-tab-relance": tab = "relance"

    db = SessionLocal()
    try:
        students  = db.query(Student).filter_by(actif=True).order_by(Student.nom).all()
        frais_all = db.query(FraisScolarite).filter_by(annee=ANNEE_COURANTE).all()
        pays_all  = db.query(Paiement).filter_by(valide=True).all()

        frais_map = {f.student_id: f for f in frais_all}
        pays_map  = {}
        for p in pays_all:
            pays_map.setdefault(p.student_id, []).append(p)

        if tab == "global":
            return _render_global(students, frais_map, pays_map)
        elif tab == "etu":
            return _render_par_etudiant(students, frais_map, pays_map)
        else:
            return _render_relances(students, frais_map, pays_map)
    finally:
        db.close()


def _render_global(students, frais_map, pays_map):
    total_du    = sum(f.montant_total for f in frais_map.values())
    total_paye  = sum(p.montant for ps in pays_map.values() for p in ps)
    total_reste = max(0, total_du - total_paye)
    nb_a_jour   = sum(1 for s in students
                      if s.id in frais_map and
                      sum(p.montant for p in pays_map.get(s.id,[])) >= frais_map[s.id].montant_total)
    nb_retard   = sum(1 for s in students if s.id in frais_map) - nb_a_jour
    taux        = round(total_paye / total_du * 100, 1) if total_du else 0

    rows = []
    for s in students:
        if s.id not in frais_map:
            continue
        f    = frais_map[s.id]
        paye = sum(p.montant for p in pays_map.get(s.id, []))
        reste = max(0, f.montant_total - paye)
        pct   = min(100, round(paye / f.montant_total * 100) if f.montant_total else 0)
        col   = "var(--green)" if reste == 0 else "var(--red)" if pct < 30 else "var(--copper)"
        rows.append(html.Tr([
            html.Td(f"{s.nom} {s.prenom}", style={"fontWeight":"600"}),
            html.Td(f"{f.montant_total:,.0f}",
                    style={"fontFamily":"JetBrains Mono,monospace","textAlign":"right"}),
            html.Td(f"{paye:,.0f}",
                    style={"fontFamily":"JetBrains Mono,monospace","color":"var(--green)",
                           "textAlign":"right","fontWeight":"700"}),
            html.Td(f"{reste:,.0f}",
                    style={"fontFamily":"JetBrains Mono,monospace","color":col,
                           "textAlign":"right","fontWeight":"700"}),
            html.Td([
                html.Div(style={"height":"6px","borderRadius":"3px","background":"var(--border)",
                                "overflow":"hidden"},
                         children=[html.Div(style={"height":"100%","width":f"{pct}%",
                                                    "background":col,"borderRadius":"3px"})]),
                html.Div(f"{pct}%", style={"fontSize":"10px","color":col,
                                           "textAlign":"right","marginTop":"2px"}),
            ]),
        ]))

    return html.Div([
        # KPIs
        html.Div([
            _kpi(f"{total_du:,.0f}", "Total du (FCFA)",    "var(--text-primary)"),
            _kpi(f"{total_paye:,.0f}", "Total recu (FCFA)",  "var(--green)"),
            _kpi(f"{total_reste:,.0f}", "Reste a percevoir",  "var(--red)"),
            _kpi(f"{taux}%",          "Taux de recouvrement","var(--gold)"),
        ], style={"display":"grid","gridTemplateColumns":"repeat(4,1fr)","gap":"16px","marginBottom":"24px"}),

        # Barre de progression globale
        html.Div([
            html.Div([
                html.Div(f"Recouvrement {ANNEE_COURANTE}", className="sga-card-title"),
                html.Div(f"{nb_a_jour} a jour — {nb_retard} en retard",
                         style={"fontSize":"12px","color":"var(--muted)","marginBottom":"12px"}),
            ]),
            html.Div(style={"height":"12px","borderRadius":"6px","background":"var(--border)","overflow":"hidden"},
                     children=[html.Div(style={"height":"100%","width":f"{taux}%",
                                               "background":"var(--green)","borderRadius":"6px",
                                               "transition":"width 1s"})]),
            html.Div(f"{taux}% encaisse", style={"fontSize":"12px","color":"var(--muted)","marginTop":"6px"}),
        ], className="sga-card", style={"marginBottom":"20px"}),

        # Tableau
        html.Div([
            html.Div(f"Detail par etudiant — {ANNEE_COURANTE}", className="sga-card-title",
                     style={"marginBottom":"16px"}),
            html.Table([
                html.Thead(html.Tr([
                    html.Th("Etudiant"), html.Th("Total du"),
                    html.Th("Paye"), html.Th("Reste"), html.Th("Avancement"),
                ])),
                html.Tbody(rows),
            ], className="sga-table", style={"width":"100%"})
            if rows else html.Div("Aucun frais configure. Cliquez sur \"+ Configurer les frais\".",
                                  style={"color":"var(--muted)","textAlign":"center","padding":"48px"}),
        ], className="sga-card"),
    ])


def _render_par_etudiant(students, frais_map, pays_map):
    cards = []
    for s in students:
        if s.id not in frais_map:
            continue
        f     = frais_map[s.id]
        pays  = pays_map.get(s.id, [])
        paye  = sum(p.montant for p in pays)
        reste = max(0, f.montant_total - paye)
        pct   = min(100, round(paye / f.montant_total * 100) if f.montant_total else 0)
        col   = "var(--green)" if reste == 0 else "var(--red)" if pct < 30 else "var(--copper)"

        historique = [html.Tr([
            html.Td(p.date_paiement.strftime("%d/%m/%Y") if p.date_paiement else "—",
                    style={"fontFamily":"JetBrains Mono,monospace","fontSize":"12px"}),
            html.Td(f"Tranche {p.tranche}", style={"color":"var(--muted)","fontSize":"12px"}),
            html.Td(html.Span(p.mode, style={"color":MODE_COLORS.get(p.mode,"var(--muted)"),
                              "fontWeight":"600","fontSize":"11px"})),
            html.Td(f"{p.montant:,.0f} FCFA",
                    style={"fontFamily":"JetBrains Mono,monospace","fontWeight":"700",
                           "color":"var(--green)","textAlign":"right"}),
            html.Td(p.reference or "—", style={"fontSize":"11px","color":"var(--muted)"}),
        ]) for p in sorted(pays, key=lambda x: x.date_paiement or date.today())]

        cards.append(html.Div([
            html.Div([
                html.Div([
                    html.Div(f"{s.nom} {s.prenom}",
                             style={"fontFamily":"Times New Roman,serif","fontSize":"18px","fontWeight":"700"}),
                    html.Div(s.email, style={"fontSize":"12px","color":"var(--muted)"}),
                ], style={"flex":"1"}),
                html.Div([
                    html.Div(f"{paye:,.0f} / {f.montant_total:,.0f}",
                             style={"fontFamily":"JetBrains Mono,monospace","fontWeight":"700",
                                    "color":col,"fontSize":"15px","textAlign":"right"}),
                    html.Div("FCFA", style={"fontSize":"10px","color":"var(--muted)","textAlign":"right"}),
                ]),
            ], style={"display":"flex","alignItems":"flex-start","marginBottom":"12px"}),

            # Barre
            html.Div(style={"height":"8px","borderRadius":"4px","background":"var(--border)",
                            "overflow":"hidden","marginBottom":"12px"},
                     children=[html.Div(style={"height":"100%","width":f"{pct}%",
                                               "background":col,"borderRadius":"4px"})]),

            # Historique
            html.Table([
                html.Thead(html.Tr([
                    html.Th("Date"), html.Th("Tranche"), html.Th("Mode"),
                    html.Th("Montant"), html.Th("Reference"),
                ])),
                html.Tbody(historique),
            ], className="sga-table", style={"width":"100%"})
            if historique else html.Div("Aucun paiement enregistre.",
                                        style={"fontSize":"12px","color":"var(--muted)","padding":"12px 0"}),
        ], className="sga-card", style={"marginBottom":"16px"}))

    if not cards:
        return html.Div("Aucun frais configure.",
                        style={"textAlign":"center","color":"var(--muted)","padding":"60px"})
    return html.Div(cards)


def _render_relances(students, frais_map, pays_map):
    en_retard = []
    for s in students:
        if s.id not in frais_map:
            continue
        f    = frais_map[s.id]
        paye = sum(p.montant for p in pays_map.get(s.id, []))
        reste = f.montant_total - paye
        if reste > 0:
            pct = round(paye / f.montant_total * 100) if f.montant_total else 0
            en_retard.append((s, f, paye, reste, pct))

    en_retard.sort(key=lambda x: x[3], reverse=True)

    if not en_retard:
        return html.Div([
            html.Div("Tous les etudiants sont a jour.",
                     style={"textAlign":"center","color":"var(--green)","fontSize":"20px",
                            "padding":"60px","fontFamily":"Times New Roman,serif","fontWeight":"700"}),
        ])

    cards = []
    for s, f, paye, reste, pct in en_retard:
        col = "var(--red)" if pct < 30 else "var(--copper)"
        urgence = "URGENT" if pct < 30 else "RELANCE"
        cards.append(html.Div([
            html.Div([
                html.Span(urgence, style={"fontSize":"9px","letterSpacing":"2px",
                          "fontWeight":"700","color":col,
                          "border":f"1px solid {col}","padding":"2px 10px",
                          "borderRadius":"2px","marginRight":"12px"}),
                html.Span(f"{s.nom} {s.prenom}", style={"fontWeight":"700","fontSize":"15px"}),
                html.Span(s.email, style={"fontSize":"12px","color":"var(--muted)","marginLeft":"12px"}),
            ], style={"display":"flex","alignItems":"center","marginBottom":"12px"}),

            html.Div([
                html.Div([
                    html.Div("Du", style={"fontSize":"10px","color":"var(--muted)","letterSpacing":"1px"}),
                    html.Div(f"{f.montant_total:,.0f} FCFA",
                             style={"fontFamily":"JetBrains Mono,monospace","fontWeight":"700"}),
                ]),
                html.Div([
                    html.Div("Paye", style={"fontSize":"10px","color":"var(--muted)","letterSpacing":"1px"}),
                    html.Div(f"{paye:,.0f} FCFA",
                             style={"fontFamily":"JetBrains Mono,monospace","color":"var(--green)","fontWeight":"700"}),
                ]),
                html.Div([
                    html.Div("Reste", style={"fontSize":"10px","color":"var(--muted)","letterSpacing":"1px"}),
                    html.Div(f"{reste:,.0f} FCFA",
                             style={"fontFamily":"JetBrains Mono,monospace","color":col,"fontWeight":"700"}),
                ]),
                html.Div([
                    html.Div("Avancement", style={"fontSize":"10px","color":"var(--muted)","letterSpacing":"1px"}),
                    html.Div(f"{pct}%", style={"fontFamily":"JetBrains Mono,monospace","color":col,"fontWeight":"700"}),
                ]),
            ], style={"display":"flex","gap":"32px","marginBottom":"12px"}),

            # Message de relance pret a copier
            html.Div([
                html.Div("Message de relance :", style={"fontSize":"10px","color":"var(--muted)",
                         "letterSpacing":"1px","marginBottom":"6px","textTransform":"uppercase"}),
                html.Div(
                    f"Madame, Monsieur, nous vous informons qu'un solde de "
                    f"{reste:,.0f} FCFA reste du pour l'annee {ANNEE_COURANTE}. "
                    f"Nous vous remercions de regulariser votre situation dans les meilleurs delais. "
                    f"Pour toute question, contactez le service scolarite.",
                    style={"fontSize":"12px","lineHeight":"1.7","color":"var(--text-primary)",
                           "fontStyle":"italic"}),
            ], style={"padding":"12px","background":"var(--bg-secondary)","borderRadius":"4px"}),
        ], className="sga-card",
           style={"marginBottom":"12px","borderLeft":f"4px solid {col}"}))

    return html.Div([
        html.Div([
            html.Div(f"{len(en_retard)} etudiant(s) en retard de paiement",
                     className="sga-card-title", style={"marginBottom":"4px"}),
            html.Div("Les messages de relance sont prets a etre copies et envoyes.",
                     style={"fontSize":"12px","color":"var(--muted)","marginBottom":"20px"}),
        ]),
        *cards,
    ])


def _kpi(val, label, color):
    return html.Div([
        html.Div(val, className="kpi-value", style={"color":color,"fontSize":"26px"}),
        html.Div(label, className="kpi-label"),
    ], className="kpi-card")
