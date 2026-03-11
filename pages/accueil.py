import dash
from dash import html, dcc

dash.register_page(__name__, path="/accueil", name="Accueil")

def layout():
    return html.Div([

        # ── NAVBAR ─────────────────────────────────────────────────────────
        html.Div([
            html.Div([
                html.Span("Nafa", style={"color":"var(--em)","fontFamily":"Instrument Serif,serif",
                    "fontSize":"24px","fontWeight":"400","letterSpacing":"1px"}),
                html.Span(" Scolaire", style={"color":"var(--text-primary)","fontFamily":"Instrument Serif,serif",
                    "fontSize":"24px","fontWeight":"400","fontStyle":"italic"}),
            ]),
            html.Div([
                html.A("Solution",        href="#solution",  className="lp-nav-link"),
                html.A("Modules",         href="#features",  className="lp-nav-link"),
                html.A("Tarifs",          href="#pricing",   className="lp-nav-link"),
                dcc.Link("Concours",      href="/concours",  className="lp-nav-link",
                         style={"color":"var(--em)","border":"1px solid var(--em)",
                                "padding":"6px 16px","borderRadius":"7px","fontWeight":"700"}),
            ], style={"display":"flex","gap":"32px","alignItems":"center"}),
            dcc.Link("Accéder à l'app →", href="/auth", className="lp-btn-primary"),
        ], className="lp-nav"),

        # ── HERO ───────────────────────────────────────────────────────────
        html.Div([
            html.Div(className="lp-grid-bg"),
            html.Div(className="lp-orb"),
            html.Div([
                html.Div("Système de Gestion Académique", className="lp-eyebrow"),
                html.H1([
                    "L'outil simple pour ",
                    html.Em("piloter votre école.")
                ], className="lp-h1"),
                html.P(
                    "Fini les tableurs éparpillés et les cahiers d'appel perdus. "
                    "Nafa Scolaire centralise tout — étudiants, présences, notes, "
                    "paiements et bulletins — en un seul endroit.",
                    className="lp-hero-sub"
                ),
                html.Div([
                    dcc.Link("Accéder à l'application →", href="/auth", className="lp-btn-primary"),
                    html.A("Voir les modules ↓", href="#features", className="lp-btn-ghost"),
                ], className="lp-hero-ctas"),
                html.Div([
                    html.Div([html.Div("10s",  className="lp-stat-val"),
                              html.Div("Pour faire l'appel", className="lp-stat-lbl")]),
                    html.Div(className="lp-stat-sep"),
                    html.Div([html.Div("1 clic", className="lp-stat-val"),
                              html.Div("Bulletins PDF", className="lp-stat-lbl")]),
                    html.Div(className="lp-stat-sep"),
                    html.Div([html.Div("100%", className="lp-stat-val"),
                              html.Div("Données locales", className="lp-stat-lbl")]),
                    html.Div(className="lp-stat-sep"),
                    html.Div([html.Div("23+", className="lp-stat-val"),
                              html.Div("Modules intégrés", className="lp-stat-lbl")]),
                ], className="lp-stats"),
            ], className="lp-hero-content"),

            html.Div([
                html.Div([
                    html.Div([
                        html.Div(style={"width":"10px","height":"10px","borderRadius":"50%","background":"#FF5F57"}),
                        html.Div(style={"width":"10px","height":"10px","borderRadius":"50%","background":"#FFBD2E"}),
                        html.Div(style={"width":"10px","height":"10px","borderRadius":"50%","background":"#28CA41"}),
                        html.Span("Nafa Scolaire — Dashboard",
                                  style={"marginLeft":"12px","fontSize":"11px",
                                         "color":"var(--muted)","fontFamily":"Plus Jakarta Sans,sans-serif"}),
                    ], style={"display":"flex","alignItems":"center","gap":"6px",
                              "padding":"12px 16px","borderBottom":"1px solid var(--border-lt)",
                              "background":"var(--bg-primary)"}),
                    html.Div([
                        _mock_kpi("60",   "Étudiants",  "var(--em)"),
                        _mock_kpi("13",   "Cours",      "var(--sable-dk)"),
                        _mock_kpi("91%",  "Présence",   "var(--em-lt)"),
                        _mock_kpi("87%",  "Scolarité",  "var(--gold)"),
                    ], style={"display":"grid","gridTemplateColumns":"repeat(4,1fr)",
                              "gap":"10px","padding":"16px"}),
                    html.Div([
                        html.Div("Présence par classe",
                                 style={"fontSize":"10px","textTransform":"uppercase",
                                        "color":"var(--muted)","marginBottom":"12px",
                                        "fontFamily":"Plus Jakarta Sans,sans-serif","letterSpacing":"1px"}),
                        html.Div([
                            _mock_bar("L1", 94, "var(--em)"),
                            _mock_bar("L2", 88, "var(--em-lt)"),
                            _mock_bar("L3", 91, "var(--sable)"),
                            _mock_bar("M1", 96, "var(--em)"),
                            _mock_bar("M2", 79, "var(--sable-dk)"),
                        ], style={"display":"flex","gap":"8px","alignItems":"flex-end","height":"80px"}),
                    ], style={"padding":"16px","borderTop":"1px solid var(--border-lt)"}),
                ], className="lp-mockup"),
            ], className="lp-hero-right"),
        ], className="lp-hero"),

        # ── TICKER ─────────────────────────────────────────────────────────
        html.Div([
            html.Div([
                *[html.Span([txt, html.Span("", style={"color":"var(--em-lt)","margin":"0 24px"})])
                  for txt in ["Appel en 10 secondes","Bulletins PDF automatisés",
                              "Migration Excel → SQL","Paiements Wave & Orange Money",
                              "Analytics avancés","Concours d'admission",
                              "Emploi du temps","Messagerie interne",
                              "Appel en 10 secondes","Bulletins PDF automatisés",
                              "Migration Excel → SQL","Paiements Wave & Orange Money"]],
            ], className="lp-ticker-inner"),
        ], className="lp-ticker"),

        # ── SOLUTION ───────────────────────────────────────────────────────
        html.Div([
            html.Div("Le constat", className="lp-section-eyebrow"),
            html.H2(["Les établissements méritent ", html.Em("mieux qu'Excel.")], className="lp-h2"),
            html.P("Les outils actuels sont lourds, chers, pensés pour l'administration — "
                   "pas pour l'enseignant devant sa classe.",
                   className="lp-section-lead"),
            html.Div([
                html.Div([
                    html.H3("✗  Avant Nafa Scolaire",
                            style={"color":"var(--red)","fontFamily":"Instrument Serif,serif",
                                   "fontSize":"22px","fontWeight":"400","marginBottom":"24px"}),
                    html.Ul([html.Li(t) for t in [
                        "Fichiers Excel éparpillés sur plusieurs ordinateurs",
                        "Cahier d'appel papier perdu en salle des profs",
                        "Bulletins générés manuellement, un par un",
                        "Aucune visibilité sur les élèves qui décrochent",
                        "ENT à 5 000€/an et 3 jours de formation",
                        "Import impossible sans développeur",
                    ]], className="lp-pain-list"),
                ], className="lp-ps-bad"),
                html.Div([
                    html.H3("✓  Avec Nafa Scolaire",
                            style={"color":"var(--green)","fontFamily":"Instrument Serif,serif",
                                   "fontSize":"22px","fontWeight":"400","marginBottom":"24px"}),
                    html.Ul([html.Li(t) for t in [
                        "Tout centralisé, une interface, accessible partout",
                        "Appel numérique en 10 secondes",
                        "Bulletins PDF de toute la promotion en un clic",
                        "Alertes automatiques dès qu'un étudiant décroche",
                        "Migration Excel → SQL en 1 clic pour vos listes",
                        "Prise en main en moins de 10 minutes",
                    ]], className="lp-gain-list"),
                ], className="lp-ps-good"),
            ], className="lp-probsol"),
        ], className="lp-section lp-section-alt", id="solution"),

        # ── MODULES ────────────────────────────────────────────────────────
        html.Div([
            html.Div("Ce qu'on fait", className="lp-section-eyebrow"),
            html.H2(["23 modules. Un seul outil. ", html.Em("Aucun compromis.")], className="lp-h2"),
            html.P("Chaque module résout un problème concret du quotidien scolaire. "
                   "Rien d'inutile, rien qui manque.", className="lp-section-lead"),

            # Grille modules complète
            html.Div([
                # Colonne 1 — Pédagogie
                html.Div([
                    html.Div(" Pédagogie", style={"fontSize":"10px","letterSpacing":"3px",
                        "textTransform":"uppercase","color":"var(--em)","fontWeight":"700",
                        "marginBottom":"16px","padding":"0 0 10px",
                        "borderBottom":"2px solid var(--em-pale)"}),
                    *[_module_row(icon, name, href) for icon, name, href in [
                        ("", "Cours & Modules",      "/cours"),
                        ("", "Appel Rapide",          "/appel"),
                        ("", "Notes & Bulletins",    "/bulletin"),
                        ("", "Emploi du temps",      "/emploi-du-temps"),
                        ("", "Calendrier",            "/calendrier"),
                        ("", "Analytics",             "/analytics"),
                        ("",  "Comparateur",          "/comparateur"),
                    ]],
                ], className="lp-module-col"),

                # Colonne 2 — Gestion
                html.Div([
                    html.Div(" Gestion", style={"fontSize":"10px","letterSpacing":"3px",
                        "textTransform":"uppercase","color":"var(--em)","fontWeight":"700",
                        "marginBottom":"16px","padding":"0 0 10px",
                        "borderBottom":"2px solid var(--em-pale)"}),
                    *[_module_row(icon, name, href) for icon, name, href in [
                        ("", "Étudiants & Fiches",  "/etudiants"),
                        ("",  "Classes & Niveaux",   "/classes"),
                        ("",  "Présences",            "/presences"),
                        ("",  "Alertes",              "/alertes"),
                        ("",  "Messagerie",           "/messagerie"),
                        ("",  "Rapports PDF",         "/rapports"),
                        ("",  "Direction",            "/direction"),
                    ]],
                ], className="lp-module-col"),

                # Colonne 3 — Administration
                html.Div([
                    html.Div(" Administration", style={"fontSize":"10px","letterSpacing":"3px",
                        "textTransform":"uppercase","color":"var(--em)","fontWeight":"700",
                        "marginBottom":"16px","padding":"0 0 10px",
                        "borderBottom":"2px solid var(--em-pale)"}),
                    *[_module_row(icon, name, href) for icon, name, href in [
                        ("", "Paiements",             "/paiements"),
                        ("", "Paiement en ligne",     "/paiement-en-ligne"),
                        ("", "Concours admission",    "/concours"),
                        ("", "Admin Concours",        "/admin-concours"),
                        ("", "Gestion Comptes",       "/gestion-comptes"),
                        ("","Secrétariat",           "/portail-secretaire"),
                        ("", "Migration Excel→SQL",   "/etudiants"),
                    ]],
                ], className="lp-module-col"),

                # Colonne 4 — Portails
                html.Div([
                    html.Div(" Portails", style={"fontSize":"10px","letterSpacing":"3px",
                        "textTransform":"uppercase","color":"var(--em)","fontWeight":"700",
                        "marginBottom":"16px","padding":"0 0 10px",
                        "borderBottom":"2px solid var(--em-pale)"}),
                    *[_module_row(icon, name, href) for icon, name, href in [
                        ("", "Espace Étudiant",      "/portail-etudiant"),
                        ("","Suivi Parent",         "/portail-parent"),
                        ("", "Portail Concours",     "/concours"),
                        ("", "Dashboard Admin",      "/"),
                    ]],
                ], className="lp-module-col"),

            ], className="lp-modules-grid"),
        ], className="lp-section", id="features"),

        # ── MIGRATION HIGHLIGHT ────────────────────────────────────────────
        html.Div([
            html.Div([
                html.Div("Nouveau", className="lp-section-eyebrow"),
                html.H2(["Migration ", html.Em("Excel → SQL"), " en 1 clic."], className="lp-h2",
                        style={"maxWidth":"500px"}),
                html.P("Importez vos listes d'étudiants existantes depuis Excel directement "
                       "dans la base de données. Colonnes détectées automatiquement, "
                       "doublons signalés, résultat immédiat.",
                       className="lp-section-lead", style={"maxWidth":"480px"}),
                html.Div([
                    html.Div([html.Span("1", style=_step_num()), html.Div([
                        html.Div("Préparez votre fichier Excel", style=_step_title()),
                        html.Div("Colonnes : Nom, Prénom, Email, Date naissance, Classe", style=_step_desc()),
                    ])], style=_step_wrap()),
                    html.Div([html.Span("2", style=_step_num()), html.Div([
                        html.Div("Glissez-déposez dans Nafa Scolaire", style=_step_title()),
                        html.Div("Interface Admin → Étudiants → Onglet Migration Excel", style=_step_desc()),
                    ])], style=_step_wrap()),
                    html.Div([html.Span("3", style=_step_num()), html.Div([
                        html.Div("Validation et import automatique", style=_step_title()),
                        html.Div("Aperçu avant import, rapport des erreurs, comptes créés", style=_step_desc()),
                    ])], style=_step_wrap()),
                ], style={"display":"flex","flexDirection":"column","gap":"16px","marginTop":"32px"}),
                html.Div([
                    dcc.Link("Essayer maintenant →", href="/etudiants", className="lp-btn-primary",
                             style={"marginTop":"32px","display":"inline-block"}),
                ]),
            ], style={"flex":"1","maxWidth":"560px"}),

            html.Div([
                html.Div([
                    html.Div([
                        html.Span("", style={"fontSize":"32px"}),
                        html.Div("etudiants_2025.xlsx",
                                 style={"fontFamily":"monospace","fontSize":"13px",
                                        "color":"var(--em)","marginTop":"8px","fontWeight":"700"}),
                        html.Div("60 lignes détectées",
                                 style={"fontSize":"11px","color":"var(--muted)","marginTop":"4px"}),
                    ], style={"textAlign":"center","padding":"24px",
                              "background":"var(--em-xpale)","borderRadius":"8px",
                              "border":"2px dashed rgba(14,102,85,0.3)","marginBottom":"16px"}),
                    html.Div("↓", style={"textAlign":"center","fontSize":"24px","color":"var(--em)",
                                         "marginBottom":"16px"}),
                    html.Div([
                        _import_row("", "FALL Demba",     "L3-STAT", "var(--em)"),
                        _import_row("", "AIDARA Ndeye",   "M1-STAT", "var(--em)"),
                        _import_row("", "MBAYE Khadija",  "L1-STAT", "var(--em)"),
                        _import_row("", "SOW Demba",      "Doublon", "var(--gold)"),
                        _import_row("", "DIOP Fatou",     "L2-STAT", "var(--em)"),
                    ], style={"background":"white","borderRadius":"8px",
                              "border":"1px solid var(--border-lt)","overflow":"hidden"}),
                    html.Div("58 importés · 2 doublons ignorés",
                             style={"textAlign":"center","fontSize":"12px","color":"var(--muted)",
                                    "marginTop":"12px","fontWeight":"600"}),
                ]),
            ], style={"flex":"1","maxWidth":"380px"}),

        ], style={"display":"flex","gap":"80px","alignItems":"flex-start"},
        className="lp-section"),

        # ── PRICING ────────────────────────────────────────────────────────
        html.Div([
            html.Div("Tarifs", className="lp-section-eyebrow"),
            html.H2(["Simple, transparent, ", html.Em("sans surprise.")], className="lp-h2"),
            html.P("Essai gratuit 30 jours sans carte bancaire. Prix adaptés en FCFA.",
                   className="lp-section-lead"),
            html.Div([
                _plan("Starter",        "75 000",  "FCFA/mois",
                      "Pour formateurs et petites structures jusqu'à 200 étudiants.",
                    ["200 étudiants maximum","5 cours maximum","Appel rapide & présences",
                     "Bulletins PDF","Alertes intelligentes"],
                    ["Analytics avancés","Migration Excel","Multi-utilisateurs"],
                    featured=False),
                _plan("Établissement", "150 000", "FCFA/mois",
                      "Pour écoles et universités privées jusqu'à 1000 étudiants.",
                    ["1000 étudiants","Cours illimités","Tous les 23 modules",
                     "Migration Excel → SQL","Analytics & Comparateur",
                     "3 comptes enseignants","Paiements Wave / Orange Money"],
                    ["API & intégrations"],
                    featured=True),
                _plan("Campus",        "Sur devis", "",
                      "Pour groupes scolaires et réseaux multi-établissements.",
                    ["Étudiants illimités","Multi-établissements","Enseignants illimités",
                     "Dashboard direction","API REST complète","Support prioritaire 24/7"],
                    [], featured=False),
            ], className="lp-pricing"),
        ], className="lp-section lp-section-alt", id="pricing"),

        # ── CTA ────────────────────────────────────────────────────────────
        html.Div([
            html.Div(className="lp-cta-orb"),
            html.Div("Passez à l'action", className="lp-section-eyebrow",
                     style={"justifyContent":"center","marginBottom":"16px"}),
            html.H2(["Prêt à transformer ", html.Em("votre établissement ?")],
                    className="lp-h2", style={"textAlign":"center","maxWidth":"600px","margin":"0 auto 20px"}),
            html.P("30 jours d'essai gratuit. Sans carte bancaire. Opérationnel en 5 minutes.",
                   style={"textAlign":"center","color":"var(--text-muted)","fontSize":"15px","marginBottom":"36px"}),
            html.Div([
                dcc.Link("Accéder à l'application →", href="/auth", className="lp-btn-primary"),
            ], style={"textAlign":"center"}),
        ], className="lp-section lp-cta-section"),

        # ── FOOTER ─────────────────────────────────────────────────────────
        html.Footer([
            html.Div([
                html.Div([
                    html.Div([
                        html.Span("Nafa", style={"color":"var(--em-lt)"}),
                        " Scolaire",
                    ], style={"fontFamily":"Instrument Serif,serif","fontSize":"24px",
                              "fontWeight":"400","marginBottom":"12px","color":"rgba(255,255,255,0.9)"}),
                    html.P("L'outil de gestion scolaire conçu pour les établissements d'Afrique francophone.",
                           style={"fontSize":"13px","color":"rgba(255,255,255,0.4)",
                                  "lineHeight":"1.8","maxWidth":"280px"}),
                ]),
                html.Div([
                    html.H4("Pédagogie", className="lp-footer-title"),
                    dcc.Link("Cours",        href="/cours",          className="lp-footer-link"),
                    dcc.Link("Appel Rapide", href="/appel",          className="lp-footer-link"),
                    dcc.Link("Bulletins",    href="/bulletin",       className="lp-footer-link"),
                    dcc.Link("Analytics",    href="/analytics",      className="lp-footer-link"),
                    dcc.Link("Calendrier",   href="/calendrier",     className="lp-footer-link"),
                ]),
                html.Div([
                    html.H4("Gestion", className="lp-footer-title"),
                    dcc.Link("Étudiants",   href="/etudiants",       className="lp-footer-link"),
                    dcc.Link("Classes",     href="/classes",         className="lp-footer-link"),
                    dcc.Link("Paiements",   href="/paiements",       className="lp-footer-link"),
                    dcc.Link("Concours",    href="/concours",        className="lp-footer-link"),
                    dcc.Link("Messagerie",  href="/messagerie",      className="lp-footer-link"),
                ]),
                html.Div([
                    html.H4("Contact", className="lp-footer-title"),
                    html.A("contact@nafascolaire.io", href="mailto:contact@nafascolaire.io",
                           className="lp-footer-link"),
                    html.A("LinkedIn", href="#", className="lp-footer-link"),
                    html.A("Mentions légales", href="#", className="lp-footer-link"),
                ]),
            ], className="lp-footer-grid"),
            html.Div([
                html.Span(" 2026 Nafa Scolaire — Tous droits réservés"),
                html.Span("Fait pour les enseignants du monde francophone"),
            ], className="lp-footer-bottom"),
        ], className="lp-footer"),

    ], className="lp-root")


# ── HELPERS ───────────────────────────────────────────────────────────────────

def _mock_kpi(val, label, color):
    return html.Div([
        html.Div(val,   style={"fontFamily":"Instrument Serif,serif","fontSize":"26px",
                               "fontWeight":"400","color":color,"lineHeight":"1"}),
        html.Div(label, style={"fontSize":"9px","textTransform":"uppercase",
                               "color":"var(--muted)","marginTop":"4px","letterSpacing":"1px"}),
    ], style={"background":"var(--bg-secondary)","border":"1px solid var(--border-lt)",
              "borderRadius":"7px","padding":"10px 12px","borderTop":f"2px solid {color}"})

def _mock_bar(label, pct, color):
    return html.Div([
        html.Div(style={"height":f"{pct}%","background":color,"borderRadius":"2px 2px 0 0",
                        "width":"100%","minHeight":"4px"}),
        html.Div(label, style={"fontSize":"8px","textAlign":"center","marginTop":"4px",
                               "color":"var(--muted)"}),
    ], style={"flex":"1","display":"flex","flexDirection":"column","justifyContent":"flex-end"})

def _module_row(icon, name, href):
    return dcc.Link([
        html.Span(icon, style={"fontSize":"14px","width":"22px","flexShrink":"0"}),
        html.Span(name, style={"fontSize":"13px","fontWeight":"500"}),
        html.Span("→", style={"marginLeft":"auto","fontSize":"11px","color":"var(--muted)"}),
    ], href=href, style={"display":"flex","alignItems":"center","gap":"10px",
                         "padding":"10px 12px","textDecoration":"none",
                         "color":"var(--text-primary)","borderRadius":"7px",
                         "transition":"all .15s","marginBottom":"2px"},
       className="lp-module-row")

def _step_num():
    return {"width":"32px","height":"32px","borderRadius":"50%",
            "background":"var(--em)","color":"white","display":"flex",
            "alignItems":"center","justifyContent":"center",
            "fontSize":"14px","fontWeight":"700","flexShrink":"0"}
def _step_title():
    return {"fontSize":"14px","fontWeight":"700","color":"var(--text-primary)","marginBottom":"4px"}
def _step_desc():
    return {"fontSize":"12px","color":"var(--muted)","lineHeight":"1.6"}
def _step_wrap():
    return {"display":"flex","gap":"16px","alignItems":"flex-start"}

def _import_row(status, name, classe, color):
    return html.Div([
        html.Span(status, style={"color":color,"fontWeight":"700","fontSize":"13px","width":"20px"}),
        html.Span(name,   style={"flex":"1","fontSize":"12px","fontWeight":"600"}),
        html.Span(classe, style={"fontSize":"11px","color":"var(--muted)","fontFamily":"monospace"}),
    ], style={"display":"flex","alignItems":"center","gap":"12px","padding":"9px 14px",
              "borderBottom":"1px solid var(--border-lt)"})

def _feat_card(icon, name, desc, badge, href):
    return html.Div([
        html.Span(icon,  className="lp-feat-icon"),
        html.Div(name,   className="lp-feat-name"),
        html.Div(desc,   className="lp-feat-desc"),
        html.Div([
            html.Span(badge, className="lp-feat-badge"),
            dcc.Link("Ouvrir →", href=href, className="lp-feat-link"),
        ], style={"display":"flex","justifyContent":"space-between","alignItems":"center","marginTop":"14px"}),
    ], className="lp-feat-card")

def _plan(name, price, per, desc, includes, excludes, featured=False):
    cls = "lp-plan lp-plan-featured" if featured else "lp-plan"
    return html.Div([
        html.Div("Le plus choisi", className="lp-plan-badge") if featured else None,
        html.Div(name,  className="lp-plan-name"),
        html.Div([
            html.Span(price, style={"fontFamily":"Instrument Serif,serif","fontSize":"42px",
                                     "fontWeight":"400","lineHeight":"1","color":"var(--em)"}),
            html.Span(" " + per, style={"fontSize":"13px","color":"var(--muted)"}),
        ], style={"marginBottom":"8px","marginTop":"8px"}),
        html.Div(desc, className="lp-plan-desc"),
        html.Ul([html.Li(f) for f in includes], className="lp-plan-includes"),
        html.Ul([html.Li(f) for f in excludes], className="lp-plan-excludes"),
        html.A("Essai gratuit 30 jours" if not featured else "Commencer maintenant",
               href="#", className="lp-plan-btn-featured" if featured else "lp-plan-btn"),
    ], className=cls)
