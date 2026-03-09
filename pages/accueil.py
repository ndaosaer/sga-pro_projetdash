import dash
from dash import html, dcc

dash.register_page(__name__, path="/accueil", name="Accueil")

def layout():
    return html.Div([

        # ── NAVBAR LANDING ─────────────────────────────────────────────────
        html.Div([
            html.Div([
                html.Span("SGA", style={"color":"var(--gold)","fontFamily":"Times New Roman,serif",
                    "fontSize":"22px","fontWeight":"700","letterSpacing":"4px"}),
                html.Span(" PRO", style={"color":"var(--text-primary)","fontFamily":"Times New Roman,serif",
                    "fontSize":"22px","fontWeight":"400","letterSpacing":"4px","fontStyle":"italic"}),
            ]),
            html.Div([
                html.A("Solution",      href="#solution",      className="lp-nav-link"),
                html.A("Fonctionnalités", href="#features",    className="lp-nav-link"),
                html.A("Tarifs",        href="#pricing",       className="lp-nav-link"),
                dcc.Link("Concours",    href="/concours",
                         style={"color":"var(--gold)","fontFamily":"JetBrains Mono,monospace",
                                "fontSize":"11px","letterSpacing":"2px","textDecoration":"none",
                                "textTransform":"uppercase","fontWeight":"700",
                                "border":"1px solid var(--gold)","padding":"6px 16px",
                                "borderRadius":"3px","transition":"all 0.2s"}),
            ], style={"display":"flex","gap":"32px"}),
            dcc.Link("Accéder à l'app →", href="/auth",
                     style={"background":"var(--gold)","color":"var(--bg-primary)",
                            "padding":"10px 24px","borderRadius":"3px",
                            "fontFamily":"JetBrains Mono,monospace","fontSize":"11px",
                            "fontWeight":"600","letterSpacing":"2px","textTransform":"uppercase",
                            "textDecoration":"none","transition":"all 0.2s"}),
        ], className="lp-nav"),

        # ── HERO ───────────────────────────────────────────────────────────
        html.Div([
            # Grille de fond décorative
            html.Div(className="lp-grid-bg"),
            # Orbe lumineuse
            html.Div(className="lp-orb"),

            html.Div([
                html.Div("Système de Gestion Académique", className="lp-eyebrow"),

                html.H1([
                    "L'OS de votre ", html.Br(),
                    html.Em("établissement scolaire.")
                ], className="lp-h1"),

                html.P(
                    "Fini les tableurs éparpillés et les cahiers d'appel perdus. "
                    "Nafa Scolaire centralise tout ce dont un enseignant a besoin — "
                    "en un seul endroit, en quelques secondes.",
                    className="lp-hero-sub"
                ),

                html.Div([
                    dcc.Link("Accéder à l'application →", href="/auth",
                             className="lp-btn-primary"),
                    html.A("Voir les fonctionnalités ↓", href="#features",
                           className="lp-btn-ghost"),
                ], className="lp-hero-ctas"),

                # Stats
                html.Div([
                    html.Div([html.Div("10s",  className="lp-stat-val"),
                              html.Div("Pour faire l'appel", className="lp-stat-lbl")]),
                    html.Div(className="lp-stat-sep"),
                    html.Div([html.Div("1 clic", className="lp-stat-val"),
                              html.Div("Pour les bulletins PDF", className="lp-stat-lbl")]),
                    html.Div(className="lp-stat-sep"),
                    html.Div([html.Div("100%", className="lp-stat-val"),
                              html.Div("Données privées", className="lp-stat-lbl")]),
                    html.Div(className="lp-stat-sep"),
                    html.Div([html.Div("10+", className="lp-stat-val"),
                              html.Div("Modules intégrés", className="lp-stat-lbl")]),
                ], className="lp-stats"),

            ], className="lp-hero-content"),

            # Mockup interface droite
            html.Div([
                html.Div([
                    # Barre de titre mockup
                    html.Div([
                        html.Div(style={"width":"10px","height":"10px","borderRadius":"50%",
                                        "background":"#FF5F57"}),
                        html.Div(style={"width":"10px","height":"10px","borderRadius":"50%",
                                        "background":"#FFBD2E"}),
                        html.Div(style={"width":"10px","height":"10px","borderRadius":"50%",
                                        "background":"#28CA41"}),
                        html.Span("Nafa Scolaire — Dashboard",
                                  style={"marginLeft":"12px","fontSize":"11px",
                                         "color":"var(--muted)","fontFamily":"JetBrains Mono,monospace"}),
                    ], style={"display":"flex","alignItems":"center","gap":"6px",
                              "padding":"12px 16px","borderBottom":"1px solid var(--border)",
                              "background":"var(--bg-secondary)"}),
                    # KPIs mockup
                    html.Div([
                        _mock_kpi("8",    "Étudiants",   "var(--gold)"),
                        _mock_kpi("4",    "Cours",       "var(--silver,#5A5650)"),
                        _mock_kpi("27",   "Séances",     "var(--copper)"),
                        _mock_kpi("13.4", "Moy. /20",    "var(--gold-dim)"),
                    ], style={"display":"grid","gridTemplateColumns":"repeat(4,1fr)",
                              "gap":"10px","padding":"16px"}),
                    # Graphique placeholder
                    html.Div([
                        html.Div("Moyennes par cours",
                                 style={"fontSize":"10px","letterSpacing":"2px",
                                        "textTransform":"uppercase","color":"var(--muted)",
                                        "marginBottom":"12px","fontFamily":"JetBrains Mono,monospace"}),
                        html.Div([
                            _mock_bar("MATH", 72, "var(--gold)"),
                            _mock_bar("INFO", 55, "#2D6A3F"),
                            _mock_bar("PHYS", 88, "var(--copper)"),
                            _mock_bar("LANG", 40, "#8B6914"),
                        ], style={"display":"flex","gap":"8px","alignItems":"flex-end","height":"80px"}),
                    ], style={"padding":"16px","borderTop":"1px solid var(--border)"}),
                ], className="lp-mockup"),
            ], className="lp-hero-right"),

        ], className="lp-hero"),

        # ── TICKER ─────────────────────────────────────────────────────────
        html.Div([
            html.Div([
                *[html.Span([txt, html.Span("◆", style={"color":"var(--gold)","margin":"0 24px"})]) 
                  for txt in ["Appel en 10 secondes","Bulletins PDF automatisés",
                              "Alertes intelligentes","Données 100% privées",
                              "Analytics avancés","Comparateur de promotion",
                              "Appel en 10 secondes","Bulletins PDF automatisés",
                              "Alertes intelligentes","Données 100% privées",
                              "Analytics avancés","Comparateur de promotion"]],
            ], className="lp-ticker-inner"),
        ], className="lp-ticker"),

        # ── PROBLÈME / SOLUTION ────────────────────────────────────────────
        html.Div([
            html.Div("Le constat", className="lp-section-eyebrow"),
            html.H2(["Les établissements méritent ", html.Em("mieux qu'Excel.")],
                    className="lp-h2"),
            html.P("Les outils actuels ont été conçus il y a 20 ans. Lourds, chers, "
                   "pensés pour l'administration — pas pour l'enseignant devant sa classe.",
                   className="lp-section-lead"),

            html.Div([
                html.Div([
                    html.H3("✗  Avant Nafa Scolaire", style={"color":"var(--red)","fontFamily":"Times New Roman,serif",
                            "fontSize":"22px","fontWeight":"700","marginBottom":"24px"}),
                    html.Ul([
                        html.Li(t) for t in [
                            "Fichiers Excel éparpillés sur plusieurs ordinateurs",
                            "Cahier d'appel papier perdu en salle des profs",
                            "Bulletins générés manuellement, un par un",
                            "Aucune visibilité sur les élèves qui décrochent",
                            "ENT à 5 000€/an et 3 jours de formation",
                            "Données élèves sur des serveurs étrangers",
                        ]
                    ], className="lp-pain-list"),
                ], className="lp-ps-bad"),

                html.Div([
                    html.H3("✓  Avec Nafa Scolaire", style={"color":"var(--green)","fontFamily":"Times New Roman,serif",
                            "fontSize":"22px","fontWeight":"700","marginBottom":"24px"}),
                    html.Ul([
                        html.Li(t) for t in [
                            "Tout centralisé, une interface, accessible partout",
                            "Appel numérique en 10 secondes depuis n'importe quel écran",
                            "Bulletins PDF de toute la promotion en un clic",
                            "Alertes automatiques dès qu'un étudiant décroche",
                            "Prise en main en moins de 10 minutes, sans formation",
                            "Données 100% locales, sous votre contrôle total",
                        ]
                    ], className="lp-gain-list"),
                ], className="lp-ps-good"),
            ], className="lp-probsol"),
        ], className="lp-section lp-section-alt", id="solution"),

        # ── FONCTIONNALITÉS ────────────────────────────────────────────────
        html.Div([
            html.Div("Ce qu'on fait", className="lp-section-eyebrow"),
            html.H2(["10 modules. Un seul outil. ", html.Em("Aucun compromis.")],
                    className="lp-h2"),
            html.P("Chaque module résout un problème concret du quotidien d'un enseignant. "
                   "Rien d'inutile, rien qui manque.",
                   className="lp-section-lead"),

            html.Div([
                _feat_card("🏠", "Dashboard",         "Vue d'ensemble en temps réel. Moyennes, progressions, absences et alertes en un coup d'œil.", "Temps réel", "/"),
                _feat_card("⚡", "Appel Rapide",      "Cartes cliquables, validation en un clic. L'appel le plus rapide du marché, chronométré.", "Signature", "/appel"),
                _feat_card("📄", "Bulletins PDF",     "Bulletins mis en page automatiquement. Export individuel ou ZIP pour toute la promotion.", "Automatisé", "/bulletin"),
                _feat_card("🔔", "Alertes",           "Détection auto des élèves en danger : absences, moyennes faibles, cours inactifs.", "Intelligent", "/alertes"),
                _feat_card("📅", "Calendrier",        "Vue mensuelle des séances avec codes couleur. Planification directe depuis la grille.", "Visuel", "/calendrier"),
                _feat_card("⚖",  "Comparateur",      "Comparez deux cours ou deux étudiants côte à côte. Radar académique inclus.", "Exclusif", "/comparateur"),
                _feat_card("📊", "Analytics",         "Violin plot, scatter, timeline, répartition des mentions. Niveau Enterprise en standard.", "Avancé", "/analytics"),
                _feat_card("🎓", "Fiches Étudiants",  "Profil académique complet, radar de compétences, historique et taux d'absence auto.", "Individuel", "/etudiants"),
                _feat_card("📚", "Gestion des Cours", "Catalogue de matières, volume horaire, progression calculée en temps réel.", "Complet", "/cours"),
            ], className="lp-features-grid"),
        ], className="lp-section", id="features"),

        # ── PRICING ────────────────────────────────────────────────────────
        html.Div([
            html.Div("Tarifs", className="lp-section-eyebrow"),
            html.H2(["Simple, transparent, ", html.Em("sans surprise.")], className="lp-h2"),
            html.P("Essai gratuit 30 jours sans carte bancaire. Résiliable à tout moment. "
                   "Prix adaptés localement (MAD, FCFA, XOF…).",
                   className="lp-section-lead"),

            html.Div([
                _plan("Starter",        "49",  "/mois", "Pour formateurs et petites structures jusqu'à 50 étudiants.",
                    ["50 étudiants maximum","5 cours maximum","Appel rapide & présences",
                     "Bulletins PDF","Alertes intelligentes"],
                    ["Analytics avancés","Comparateur","Multi-utilisateurs"],
                    featured=False),
                _plan("Établissement", "199", "/mois", "Pour écoles et universités privées jusqu'à 500 étudiants.",
                    ["500 étudiants","Cours illimités","Tous les modules inclus",
                     "Analytics & Comparateur","Export ZIP bulletins","3 comptes enseignants"],
                    ["API & intégrations"],
                    featured=True),
                _plan("Campus",        "599", "/mois", "Pour groupes scolaires et réseaux multi-établissements.",
                    ["Étudiants illimités","Multi-établissements","Enseignants illimités",
                     "Dashboard direction","API REST complète","Support prioritaire 24/7"],
                    [],
                    featured=False),
            ], className="lp-pricing"),
        ], className="lp-section lp-section-alt", id="pricing"),

        # ── CTA FINAL ──────────────────────────────────────────────────────
        html.Div([
            html.Div(className="lp-cta-orb"),
            html.Div("Passez à l'action", className="lp-section-eyebrow",
                     style={"justifyContent":"center","marginBottom":"16px"}),
            html.H2(["Prêt à transformer ", html.Em("votre établissement ?")],
                    className="lp-h2", style={"textAlign":"center","maxWidth":"600px","margin":"0 auto 20px"}),
            html.P("30 jours d'essai gratuit. Sans carte bancaire. Opérationnel en 5 minutes.",
                   style={"textAlign":"center","color":"var(--muted)","fontSize":"15px","marginBottom":"36px"}),
            html.Div([
                dcc.Link("Accéder à l'application →", href="/auth",
                         className="lp-btn-primary"),
            ], style={"textAlign":"center"}),
        ], className="lp-section lp-cta-section"),

        # ── FOOTER ─────────────────────────────────────────────────────────
        html.Footer([
            html.Div([
                html.Div([
                    html.Div([
                        html.Span("SGA", style={"color":"var(--gold)"}),
                        " PRO",
                    ], style={"fontFamily":"Times New Roman,serif","fontSize":"24px",
                              "fontWeight":"700","letterSpacing":"4px","marginBottom":"12px",
                              "color":"rgba(245,240,230,0.9)"}),
                    html.P("L'OS des établissements scolaires. Conçu pour les enseignants, "
                           "déployé en 5 minutes, adopté pour toujours.",
                           style={"fontSize":"13px","color":"rgba(245,240,230,0.4)",
                                  "lineHeight":"1.8","maxWidth":"280px"}),
                ]),
                html.Div([
                    html.H4("Produit", className="lp-footer-title"),
                    html.A("Fonctionnalités", href="#features", className="lp-footer-link"),
                    html.A("Tarifs",          href="#pricing",  className="lp-footer-link"),
                    html.A("Roadmap",         href="#",         className="lp-footer-link"),
                ]),
                html.Div([
                    html.H4("Application", className="lp-footer-title"),
                    dcc.Link("Dashboard",  href="/auth",            className="lp-footer-link"),
                    dcc.Link("Cours",      href="/cours",       className="lp-footer-link"),
                    dcc.Link("Étudiants",  href="/etudiants",   className="lp-footer-link"),
                    dcc.Link("Concours",   href="/concours",    className="lp-footer-link"),
                    dcc.Link("Analytics",  href="/analytics",   className="lp-footer-link"),
                ]),
                html.Div([
                    html.H4("Contact", className="lp-footer-title"),
                    html.A("contact@sgapro.io", href="mailto:contact@sgapro.io", className="lp-footer-link"),
                    html.A("LinkedIn",           href="#",                        className="lp-footer-link"),
                    html.A("Mentions légales",   href="#",                        className="lp-footer-link"),
                ]),
            ], className="lp-footer-grid"),
            html.Div([
                html.Span("© 2026 Nafa Scolaire — Tous droits réservés"),
                html.Span("Fait pour les enseignants du monde francophone ◆"),
            ], className="lp-footer-bottom"),
        ], className="lp-footer"),

    ], className="lp-root")


# ── HELPERS ───────────────────────────────────────────────────────────────────

def _mock_kpi(val, label, color):
    return html.Div([
        html.Div(val,   style={"fontFamily":"Times New Roman,serif","fontSize":"28px",
                               "fontWeight":"700","color":color,"lineHeight":"1"}),
        html.Div(label, style={"fontSize":"9px","letterSpacing":"2px","textTransform":"uppercase",
                               "color":"var(--muted)","marginTop":"4px",
                               "fontFamily":"JetBrains Mono,monospace"}),
    ], style={"background":"var(--bg-secondary)","border":"1px solid var(--border)",
              "borderRadius":"4px","padding":"10px 12px","borderTop":f"2px solid {color}"})


def _mock_bar(label, pct, color):
    return html.Div([
        html.Div(style={"height":f"{pct}%","background":color,"borderRadius":"2px 2px 0 0",
                        "width":"100%","minHeight":"4px"}),
        html.Div(label, style={"fontSize":"8px","textAlign":"center","marginTop":"4px",
                               "color":"var(--muted)","fontFamily":"JetBrains Mono,monospace"}),
    ], style={"flex":"1","display":"flex","flexDirection":"column","justifyContent":"flex-end"})


def _feat_card(icon, name, desc, badge, href):
    return html.Div([
        html.Span(icon,  className="lp-feat-icon"),
        html.Div(name,   className="lp-feat-name"),
        html.Div(desc,   className="lp-feat-desc"),
        html.Div([
            html.Span(badge, className="lp-feat-badge"),
            dcc.Link("Ouvrir →", href=href, className="lp-feat-link"),
        ], style={"display":"flex","justifyContent":"space-between","alignItems":"center",
                  "marginTop":"14px"}),
    ], className="lp-feat-card")


def _plan(name, price, per, desc, includes, excludes, featured=False):
    cls = "lp-plan lp-plan-featured" if featured else "lp-plan"
    return html.Div([
        html.Div("Le plus choisi", className="lp-plan-badge") if featured else None,
        html.Div(name,  className="lp-plan-name"),
        html.Div([
            html.Span("€", style={"fontSize":"22px","color":"var(--gold)","verticalAlign":"top",
                                   "marginTop":"14px","display":"inline-block"}),
            html.Span(price, style={"fontFamily":"Times New Roman,serif","fontSize":"56px",
                                     "fontWeight":"700","lineHeight":"1"}),
            html.Span(per,   style={"fontSize":"14px","color":"var(--muted)",
                                     "fontFamily":"JetBrains Mono,monospace"}),
        ], style={"marginBottom":"8px"}),
        html.Div(desc, className="lp-plan-desc"),
        html.Ul([html.Li(f) for f in includes], className="lp-plan-includes"),
        html.Ul([html.Li(f) for f in excludes], className="lp-plan-excludes"),
        html.A("Essai gratuit 30 jours" if not featured else "Commencer maintenant",
               href="#", className="lp-plan-btn-featured" if featured else "lp-plan-btn"),
    ], className=cls)
