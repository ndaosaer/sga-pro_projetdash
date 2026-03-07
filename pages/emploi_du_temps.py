import dash, io, base64
from dash import html, dcc, Input, Output, State, callback, ctx
from database import SessionLocal
from models import Course, Creneau
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

dash.register_page(__name__, path="/emploi-du-temps", name="Emploi du temps")

JOURS       = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
HEURES      = [h / 2 for h in range(16, 37)]   # 8h00 a 18h00 par demi-heure
HEURE_DEBUT = 8.0
HEURE_FIN   = 18.0
SLOT_H      = 48   # hauteur px par demi-heure
GRID_TOP    = 40   # hauteur entete
COL_W       = 160  # largeur colonne jour
COL_LABEL   = 56   # largeur colonne heures

GOLD   = "#B8922A"
DARK   = "#1A1712"
BORDER = "#E5E0D8"


def _fmt_h(h):
    """8.5 -> '08h30'"""
    hh = int(h)
    mm = int((h - hh) * 60)
    return f"{hh:02d}h{mm:02d}"


def _slots_from(debut, fin):
    """Retourne l'index de ligne (0 = 8h00) et la hauteur en slots de 30min."""
    row    = int((debut - HEURE_DEBUT) * 2)
    height = int((fin - debut) * 2)
    return row, height


def layout():
    return html.Div([
        dcc.Store(id="edt-refresh", data=0),
        dcc.Store(id="edt-vue",     data="semaine"),
        dcc.Download(id="edt-download"),

        html.Div([
            html.Div([
                html.Div("Emploi du temps", className="page-title"),
                html.Div("Planning hebdomadaire", className="page-subtitle"),
            ]),
            html.Div([
                html.Button("Export PDF",         id="btn-edt-pdf",    n_clicks=0, className="btn-sga"),
                html.Button("+ Ajouter un cours", id="btn-edt-new",    n_clicks=0, className="btn-sga btn-gold"),
            ], style={"display":"flex","gap":"8px"}),
        ], className="topbar"),

        html.Div([
            # Filtres
            html.Div([
                html.Div([
                    html.Button("Semaine",    id="vue-semaine",    n_clicks=0, className="btn-sga btn-gold"),
                    html.Button("Enseignant", id="vue-enseignant", n_clicks=0, className="btn-sga"),
                    html.Button("Salles",     id="vue-salle",      n_clicks=0, className="btn-sga"),
                ], style={"display":"flex","gap":"8px","marginBottom":"16px"}),

                html.Div([
                    html.Div([
                        html.Div("Filtrer par enseignant", className="sga-label"),
                        dcc.Dropdown(id="edt-filter-ens", placeholder="Tous",
                                     clearable=True, style={"minWidth":"200px"}),
                    ]),
                    html.Div([
                        html.Div("Filtrer par salle", className="sga-label"),
                        dcc.Dropdown(id="edt-filter-salle", placeholder="Toutes",
                                     clearable=True, style={"minWidth":"200px"}),
                    ]),
                ], style={"display":"flex","gap":"24px","marginBottom":"20px"}),
            ]),

            # Alertes conflits
            html.Div(id="edt-conflits"),

            # Grille
            html.Div(id="edt-grille", style={"overflowX":"auto"}),

        ], style={"padding":"24px"}),

        # ── Modal ajout creneau ──
        html.Div([
            html.Div([
                html.Div("Ajouter un creneau", className="sga-card-title",
                         style={"marginBottom":"20px"}),
                html.Div([
                    html.Div([
                        html.Div("Cours", className="sga-label"),
                        dcc.Dropdown(id="edt-nc-cours", placeholder="Selectionner...",
                                     clearable=False),
                    ], style={"flex":"2"}),
                    html.Div([
                        html.Div("Jour", className="sga-label"),
                        dcc.Dropdown(id="edt-nc-jour",
                                     options=[{"label":j,"value":i} for i,j in enumerate(JOURS)],
                                     placeholder="Jour", clearable=False),
                    ], style={"flex":"1"}),
                ], style={"display":"flex","gap":"16px","marginBottom":"14px"}),
                html.Div([
                    html.Div([
                        html.Div("Heure de debut", className="sga-label"),
                        dcc.Dropdown(id="edt-nc-debut",
                                     options=[{"label":_fmt_h(h),"value":h} for h in HEURES[:-1]],
                                     placeholder="08h00", clearable=False),
                    ], style={"flex":"1"}),
                    html.Div([
                        html.Div("Heure de fin", className="sga-label"),
                        dcc.Dropdown(id="edt-nc-fin",
                                     options=[{"label":_fmt_h(h),"value":h} for h in HEURES[1:]],
                                     placeholder="10h00", clearable=False),
                    ], style={"flex":"1"}),
                ], style={"display":"flex","gap":"16px","marginBottom":"14px"}),
                html.Div([
                    html.Div([
                        html.Div("Salle", className="sga-label"),
                        dcc.Input(id="edt-nc-salle", placeholder="ex: Amphi A, Salle 12",
                                  className="sga-input", style={"width":"100%"}),
                    ], style={"flex":"1"}),
                    html.Div([
                        html.Div("Enseignant", className="sga-label"),
                        dcc.Input(id="edt-nc-ens", placeholder="Nom de l'enseignant",
                                  className="sga-input", style={"width":"100%"}),
                    ], style={"flex":"1"}),
                ], style={"display":"flex","gap":"16px","marginBottom":"20px"}),
                html.Div([
                    html.Button("Ajouter", id="btn-edt-save",   n_clicks=0, className="btn-sga btn-gold"),
                    html.Button("Annuler", id="btn-edt-cancel", n_clicks=0, className="btn-sga"),
                ], style={"display":"flex","gap":"10px"}),
                html.Div(id="edt-nc-feedback", style={"marginTop":"12px"}),
            ], style={"background":"var(--bg-card)","border":"1px solid var(--border)",
                      "borderRadius":"6px","padding":"32px","width":"560px","margin":"0 auto"}),
        ], id="modal-edt",
           style={"display":"none","position":"fixed","inset":"0",
                  "background":"rgba(0,0,0,0.5)","zIndex":"999",
                  "alignItems":"center","justifyContent":"center"}),
    ])


# ── Charger les filtres ──
@callback(
    Output("edt-nc-cours",      "options"),
    Output("edt-filter-ens",    "options"),
    Output("edt-filter-salle",  "options"),
    Input("edt-refresh", "data"),
)
def load_options(refresh):
    db = SessionLocal()
    try:
        courses  = db.query(Course).order_by(Course.libelle).all()
        creneaux = db.query(Creneau).all()
        cours_opts = [{"label":f"{c.code} — {c.libelle}","value":c.code} for c in courses]
        ens_set   = sorted({cr.enseignant for cr in creneaux if cr.enseignant})
        salle_set = sorted({cr.salle for cr in creneaux if cr.salle})
        return (cours_opts,
                [{"label":e,"value":e} for e in ens_set],
                [{"label":s,"value":s} for s in salle_set])
    finally:
        db.close()


# ── Toggle modal ──
@callback(
    Output("modal-edt","style"),
    Input("btn-edt-new","n_clicks"),
    Input("btn-edt-cancel","n_clicks"),
    Input("btn-edt-save","n_clicks"),
    prevent_initial_call=True,
)
def toggle_modal(n1, n2, n3):
    show = {"display":"flex","position":"fixed","inset":"0","background":"rgba(0,0,0,0.5)",
            "zIndex":"999","alignItems":"center","justifyContent":"center"}
    if ctx.triggered_id == "btn-edt-new":
        return show
    return {"display":"none"}


# ── Sauvegarder creneau ──
@callback(
    Output("edt-nc-feedback","children"),
    Output("edt-refresh","data", allow_duplicate=True),
    Input("btn-edt-save","n_clicks"),
    State("edt-nc-cours","value"),
    State("edt-nc-jour","value"),
    State("edt-nc-debut","value"),
    State("edt-nc-fin","value"),
    State("edt-nc-salle","value"),
    State("edt-nc-ens","value"),
    State("edt-refresh","data"),
    prevent_initial_call=True,
)
def sauver_creneau(n, cours, jour, debut, fin, salle, ens, refresh):
    if not all([cours, jour is not None, debut, fin]):
        return html.Div("Cours, jour et horaires sont requis.",
                        className="sga-alert sga-alert-warning"), dash.no_update
    if fin <= debut:
        return html.Div("L'heure de fin doit etre apres l'heure de debut.",
                        className="sga-alert sga-alert-warning"), dash.no_update

    db = SessionLocal()
    try:
        # Recuperer la couleur du cours
        course = db.query(Course).filter_by(code=cours).first()
        couleur = course.couleur if course else GOLD

        cr = Creneau()
        cr.course_code = cours
        cr.jour        = int(jour)
        cr.heure_debut = float(debut)
        cr.heure_fin   = float(fin)
        cr.salle       = salle or ""
        cr.enseignant  = ens or (course.enseignant if course else "")
        cr.couleur     = couleur
        cr.created_at  = datetime.now()
        db.add(cr)
        db.commit()
        return html.Div("Creneau ajoute.", className="sga-alert sga-alert-success"), (refresh or 0)+1
    except Exception as e:
        db.rollback()
        return html.Div(str(e), className="sga-alert sga-alert-danger"), dash.no_update
    finally:
        db.close()


# ── Vue active ──
@callback(
    Output("edt-vue","data"),
    Input("vue-semaine","n_clicks"),
    Input("vue-enseignant","n_clicks"),
    Input("vue-salle","n_clicks"),
    prevent_initial_call=True,
)
def change_vue(n1, n2, n3):
    mapping = {"vue-semaine":"semaine","vue-enseignant":"enseignant","vue-salle":"salle"}
    return mapping.get(ctx.triggered_id, "semaine")


# ── Rendu grille + conflits ──
@callback(
    Output("edt-grille","children"),
    Output("edt-conflits","children"),
    Input("edt-vue","data"),
    Input("edt-refresh","data"),
    Input("edt-filter-ens","value"),
    Input("edt-filter-salle","value"),
)
def render_grille(vue, refresh, filter_ens, filter_salle):
    db = SessionLocal()
    try:
        creneaux = db.query(Creneau).all()
        courses  = {c.code: c for c in db.query(Course).all()}
    finally:
        db.close()

    # Appliquer filtres
    if filter_ens:
        creneaux = [cr for cr in creneaux if cr.enseignant == filter_ens]
    if filter_salle:
        creneaux = [cr for cr in creneaux if cr.salle == filter_salle]

    # Detecter conflits
    conflits = _detecter_conflits(creneaux)
    conflits_elem = _render_conflits(conflits) if conflits else html.Div()

    if vue == "semaine":
        grille = _render_grille_semaine(creneaux, courses)
    elif vue == "enseignant":
        grille = _render_vue_enseignant(creneaux, courses)
    else:
        grille = _render_vue_salle(creneaux, courses)

    return grille, conflits_elem


def _detecter_conflits(creneaux):
    """Detecte les creneaux qui se chevauchent sur le meme jour et la meme salle."""
    conflits = []
    for i, a in enumerate(creneaux):
        for b in creneaux[i+1:]:
            if a.jour != b.jour:
                continue
            # Meme salle non vide
            if a.salle and b.salle and a.salle == b.salle:
                if a.heure_debut < b.heure_fin and b.heure_debut < a.heure_fin:
                    conflits.append((a, b, "salle"))
            # Meme enseignant non vide
            if a.enseignant and b.enseignant and a.enseignant == b.enseignant:
                if a.heure_debut < b.heure_fin and b.heure_debut < a.heure_fin:
                    conflits.append((a, b, "enseignant"))
    return conflits


def _render_conflits(conflits):
    items = []
    for a, b, type_conflit in conflits:
        items.append(html.Div([
            html.Span("CONFLIT", style={"fontSize":"9px","letterSpacing":"2px","fontWeight":"700",
                      "color":"var(--red)","border":"1px solid var(--red)",
                      "padding":"2px 8px","borderRadius":"2px","marginRight":"10px"}),
            html.Span(f"{JOURS[a.jour]} {_fmt_h(a.heure_debut)}-{_fmt_h(a.heure_fin)} : ",
                      style={"fontSize":"12px","fontWeight":"600"}),
            html.Span(f"{a.course_code} et {b.course_code} — meme {type_conflit} ({a.salle or a.enseignant})",
                      style={"fontSize":"12px","color":"var(--muted)"}),
        ], style={"display":"flex","alignItems":"center","padding":"10px 14px",
                  "background":"rgba(139,37,0,0.08)","borderRadius":"4px",
                  "marginBottom":"6px","borderLeft":"3px solid var(--red)"}))
    return html.Div([
        html.Div(f"{len(conflits)} conflit(s) detecte(s)", style={
            "fontSize":"11px","letterSpacing":"2px","textTransform":"uppercase",
            "color":"var(--red)","fontWeight":"700","marginBottom":"10px"}),
        *items,
    ], style={"marginBottom":"20px","padding":"16px","background":"var(--bg-card)",
              "border":"1px solid var(--red)","borderRadius":"6px"})


def _render_grille_semaine(creneaux, courses):
    """Grille CSS position absolue — chaque creneau est place par top/height."""
    nb_slots = int((HEURE_FIN - HEURE_DEBUT) * 2)  # 20 slots de 30min
    total_w  = COL_LABEL + COL_W * 5

    # Colonne heures
    heure_labels = []
    for i, h in enumerate(HEURES):
        if h == int(h):  # afficher seulement les heures pleines
            heure_labels.append(html.Div(_fmt_h(h), style={
                "position":"absolute","top":f"{GRID_TOP + i * SLOT_H}px",
                "width":f"{COL_LABEL}px","fontSize":"10px","color":"var(--muted)",
                "textAlign":"right","paddingRight":"8px","lineHeight":"1",
                "transform":"translateY(-50%)"}))

    # Lignes horizontales
    lignes = []
    for i in range(nb_slots + 1):
        h = HEURE_DEBUT + i * 0.5
        is_full = (h == int(h))
        lignes.append(html.Div(style={
            "position":"absolute","left":f"{COL_LABEL}px","right":"0",
            "top":f"{GRID_TOP + i * SLOT_H}px","height":"1px",
            "background":"var(--border)" if is_full else "rgba(229,224,216,0.4)"}))

    # En-tetes jours
    entetes = []
    for j, jour in enumerate(JOURS):
        entetes.append(html.Div(jour, style={
            "position":"absolute","top":"0","height":f"{GRID_TOP}px",
            "left":f"{COL_LABEL + j * COL_W}px","width":f"{COL_W}px",
            "display":"flex","alignItems":"center","justifyContent":"center",
            "fontFamily":"JetBrains Mono,monospace","fontSize":"11px",
            "letterSpacing":"3px","textTransform":"uppercase","color":"var(--muted)",
            "fontWeight":"700","borderBottom":"2px solid var(--gold)"}))

    # Creneaux
    blocs = []
    for cr in creneaux:
        row, height = _slots_from(cr.heure_debut, cr.heure_fin)
        top  = GRID_TOP + row * SLOT_H
        h_px = height * SLOT_H - 3
        left = COL_LABEL + cr.jour * COL_W + 3
        w    = COL_W - 6
        col  = cr.couleur or GOLD
        course = courses.get(cr.course_code)
        libelle = course.libelle if course else cr.course_code

        blocs.append(html.Div([
            html.Div(cr.course_code, style={"fontWeight":"700","fontSize":"11px",
                     "letterSpacing":"1px","marginBottom":"2px"}),
            html.Div(libelle, style={"fontSize":"10px","opacity":"0.85",
                     "overflow":"hidden","textOverflow":"ellipsis","whiteSpace":"nowrap"}),
            html.Div(f"{_fmt_h(cr.heure_debut)}—{_fmt_h(cr.heure_fin)}",
                     style={"fontSize":"9px","opacity":"0.75","marginTop":"3px"}),
            html.Div(cr.salle or "", style={"fontSize":"9px","opacity":"0.7",
                     "overflow":"hidden","textOverflow":"ellipsis","whiteSpace":"nowrap"}),
        ], style={
            "position":"absolute","top":f"{top}px","left":f"{left}px",
            "width":f"{w}px","height":f"{h_px}px",
            "background":col,"borderRadius":"4px","padding":"6px 8px",
            "color":_contraste(col),"overflow":"hidden","cursor":"default",
            "boxShadow":"0 2px 6px rgba(0,0,0,0.15)","fontSize":"11px",
        }, id={"type":"edt-bloc","index":cr.id},
           title=f"{libelle}\n{_fmt_h(cr.heure_debut)}–{_fmt_h(cr.heure_fin)}\n{cr.enseignant or ''}\n{cr.salle or ''}"))

    total_h = GRID_TOP + nb_slots * SLOT_H + 20

    return html.Div([
        html.Div(
            heure_labels + lignes + entetes + blocs,
            style={"position":"relative","width":f"{total_w}px","height":f"{total_h}px",
                   "userSelect":"none"}),
    ], style={"overflowX":"auto","background":"var(--bg-card)","border":"1px solid var(--border)",
              "borderRadius":"6px","padding":"16px"})


def _render_vue_enseignant(creneaux, courses):
    """Groupe les creneaux par enseignant."""
    par_ens = {}
    for cr in creneaux:
        key = cr.enseignant or "Non assigne"
        par_ens.setdefault(key, []).append(cr)

    if not par_ens:
        return html.Div("Aucun creneau.", style={"color":"var(--muted)","padding":"40px","textAlign":"center"})

    cards = []
    for ens, crs in sorted(par_ens.items()):
        par_jour = {j: [] for j in range(5)}
        for cr in crs:
            par_jour[cr.jour].append(cr)
        total_h = sum(cr.heure_fin - cr.heure_debut for cr in crs)

        rows = []
        for jour_idx in range(5):
            for cr in sorted(par_jour[jour_idx], key=lambda x: x.heure_debut):
                course = courses.get(cr.course_code)
                col    = cr.couleur or GOLD
                rows.append(html.Tr([
                    html.Td(JOURS[cr.jour], style={"fontWeight":"600","fontSize":"12px"}),
                    html.Td(f"{_fmt_h(cr.heure_debut)} — {_fmt_h(cr.heure_fin)}",
                            style={"fontFamily":"JetBrains Mono,monospace","fontSize":"12px"}),
                    html.Td(html.Span(cr.course_code,
                                      style={"background":col,"color":_contraste(col),
                                             "padding":"2px 8px","borderRadius":"3px",
                                             "fontSize":"11px","fontWeight":"700"})),
                    html.Td(course.libelle if course else "—",
                            style={"fontSize":"12px","color":"var(--muted)"}),
                    html.Td(cr.salle or "—", style={"fontSize":"12px","color":"var(--muted)"}),
                ]))

        cards.append(html.Div([
            html.Div([
                html.Div(ens, style={"fontFamily":"Times New Roman,serif","fontSize":"18px",
                         "fontWeight":"700","flex":"1"}),
                html.Div(f"{total_h:.1f}h / semaine",
                         style={"fontFamily":"JetBrains Mono,monospace","fontSize":"13px",
                                "color":GOLD,"fontWeight":"700"}),
            ], style={"display":"flex","alignItems":"center","marginBottom":"12px"}),
            html.Table([
                html.Thead(html.Tr([html.Th("Jour"),html.Th("Horaire"),
                                    html.Th("Code"),html.Th("Matiere"),html.Th("Salle")])),
                html.Tbody(rows),
            ], className="sga-table", style={"width":"100%"}),
        ], className="sga-card", style={"marginBottom":"16px"}))

    return html.Div(cards)


def _render_vue_salle(creneaux, courses):
    """Groupe les creneaux par salle."""
    par_salle = {}
    for cr in creneaux:
        key = cr.salle or "Salle non definie"
        par_salle.setdefault(key, []).append(cr)

    if not par_salle:
        return html.Div("Aucun creneau.", style={"color":"var(--muted)","padding":"40px","textAlign":"center"})

    cards = []
    for salle, crs in sorted(par_salle.items()):
        total_h   = sum(cr.heure_fin - cr.heure_debut for cr in crs)
        taux_occ  = round(total_h / (5 * (HEURE_FIN - HEURE_DEBUT)) * 100)

        rows = []
        for cr in sorted(crs, key=lambda x: (x.jour, x.heure_debut)):
            course = courses.get(cr.course_code)
            col    = cr.couleur or GOLD
            rows.append(html.Tr([
                html.Td(JOURS[cr.jour], style={"fontWeight":"600","fontSize":"12px"}),
                html.Td(f"{_fmt_h(cr.heure_debut)} — {_fmt_h(cr.heure_fin)}",
                        style={"fontFamily":"JetBrains Mono,monospace","fontSize":"12px"}),
                html.Td(html.Span(cr.course_code,
                                  style={"background":col,"color":_contraste(col),
                                         "padding":"2px 8px","borderRadius":"3px",
                                         "fontSize":"11px","fontWeight":"700"})),
                html.Td(course.libelle if course else "—",
                        style={"fontSize":"12px","color":"var(--muted)"}),
                html.Td(cr.enseignant or "—", style={"fontSize":"12px","color":"var(--muted)"}),
            ]))

        col_taux = "#2D6A3F" if taux_occ < 60 else "#8B5E3C" if taux_occ < 85 else "#8B2500"
        cards.append(html.Div([
            html.Div([
                html.Div(salle, style={"fontFamily":"Times New Roman,serif","fontSize":"18px",
                         "fontWeight":"700","flex":"1"}),
                html.Div([
                    html.Div(f"{taux_occ}%", style={"fontFamily":"JetBrains Mono,monospace",
                             "fontSize":"20px","fontWeight":"700","color":col_taux}),
                    html.Div("occupation", style={"fontSize":"10px","color":"var(--muted)"}),
                ], style={"textAlign":"right"}),
            ], style={"display":"flex","alignItems":"center","marginBottom":"8px"}),
            html.Div(style={"height":"6px","borderRadius":"3px","background":"var(--border)",
                            "overflow":"hidden","marginBottom":"12px"},
                     children=[html.Div(style={"height":"100%","width":f"{taux_occ}%",
                                               "background":col_taux,"borderRadius":"3px"})]),
            html.Table([
                html.Thead(html.Tr([html.Th("Jour"),html.Th("Horaire"),
                                    html.Th("Code"),html.Th("Matiere"),html.Th("Enseignant")])),
                html.Tbody(rows),
            ], className="sga-table", style={"width":"100%"}),
        ], className="sga-card", style={"marginBottom":"16px"}))

    return html.Div(cards)


# ── Export PDF ──
@callback(
    Output("edt-download","data"),
    Input("btn-edt-pdf","n_clicks"),
    prevent_initial_call=True,
)
def export_pdf(n):
    db = SessionLocal()
    try:
        creneaux = db.query(Creneau).all()
        courses  = {c.code: c for c in db.query(Course).all()}
    finally:
        db.close()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4),
                            leftMargin=1.5*cm, rightMargin=1.5*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("title", parent=styles["Title"],
                                 fontSize=18, textColor=colors.HexColor("#B8922A"),
                                 spaceAfter=12)
    elements = [Paragraph("Emploi du temps", title_style), Spacer(1, 0.3*cm)]

    # Construire la grille
    heures_pleines = [h for h in HEURES if h == int(h)]
    header = [""] + JOURS
    data   = [header]

    for h in heures_pleines:
        row = [_fmt_h(h)]
        for j in range(5):
            crs_slot = [cr for cr in creneaux
                        if cr.jour == j and cr.heure_debut <= h < cr.heure_fin]
            if crs_slot:
                cr = crs_slot[0]
                course = courses.get(cr.course_code)
                libelle = course.libelle[:20] if course else cr.course_code
                row.append(f"{cr.course_code}\n{libelle}\n{cr.salle or ''}")
            else:
                row.append("")
        data.append(row)

    col_widths = [2*cm] + [4.5*cm]*5
    t = Table(data, colWidths=col_widths, rowHeights=[0.8*cm]*len(data))
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,0),  colors.HexColor("#1A1712")),
        ("TEXTCOLOR",   (0,0), (-1,0),  colors.HexColor("#B8922A")),
        ("FONTNAME",    (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,0),  9),
        ("BACKGROUND",  (0,1), (0,-1),  colors.HexColor("#F5F0E6")),
        ("FONTSIZE",    (0,0), (-1,-1), 7),
        ("GRID",        (0,0), (-1,-1), 0.5, colors.HexColor("#E5E0D8")),
        ("ALIGN",       (0,0), (-1,-1), "CENTER"),
        ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
        ("WORDWRAP",    (0,0), (-1,-1), True),
    ]))
    elements.append(t)
    doc.build(elements)

    buf.seek(0)
    return dcc.send_bytes(buf.read(), "emploi_du_temps.pdf")


def _contraste(hex_color):
    """Retourne noir ou blanc selon la luminosite du fond."""
    try:
        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
        luminance = (0.299*r + 0.587*g + 0.114*b) / 255
        return "#1A1712" if luminance > 0.5 else "#F5F0E6"
    except Exception:
        return "#F5F0E6"
