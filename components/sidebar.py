from dash import html, dcc
from database import SessionLocal, init_db
from models import Notification

ROLE_LABELS = {
    "admin":     ("Directeur",  ""),
    "teacher":   ("Enseignant", ""),
    "secretary": ("Secrétaire", ""),
}

# Menus selon le rôle
NAV_BY_ROLE = {
    "admin": [
        ("Navigation", [
            {"icon":"",  "label":"Accueil",        "href":"/accueil"},
            {"icon":"",  "label":"Dashboard",       "href":"/"},
            {"icon":"",  "label":"Cours",           "href":"/cours"},
            {"icon":"",  "label":"Présences",       "href":"/presences"},
            {"icon":"",  "label":"Étudiants",       "href":"/etudiants"},
            {"icon":"",  "label":"Analytics",       "href":"/analytics"},
        ]),
        ("Outils", [
            {"icon":"", "label":"Appel Rapide",    "href":"/appel"},
            {"icon":"",  "label":"Paiements",       "href":"/paiements"},
            {"icon":"",  "label":"Messagerie",      "href":"/messagerie"},
            {"icon":"", "label":"Alertes",         "href":"/alertes"},
            {"icon":"", "label":"Bulletins PDF",   "href":"/bulletin"},
            {"icon":"", "label":"Calendrier",      "href":"/calendrier"},
            {"icon":"",  "label":"Emploi du temps","href":"/emploi-du-temps"},
            {"icon":"",  "label":"Comparateur",    "href":"/comparateur"},
        ]),
        ("Admin", [
            {"icon":"", "label":"Gestion comptes", "href":"/gestion-comptes"},
            {"icon":"", "label":"Classes",         "href":"/classes"},
            {"icon":"",  "label":"Concours",        "href":"/admin-concours"},
            {"icon":"",  "label":"TB Direction",    "href":"/direction"},
            {"icon":"", "label":"Rapports PDF",   "href":"/rapports"},
            {"icon":"", "label":"Paiement online","href":"/paiement-en-ligne"},
        ]),
    ],
    "teacher": [
        ("Navigation", [
            {"icon":"",  "label":"Accueil",        "href":"/accueil"},
            {"icon":"",  "label":"Dashboard",      "href":"/"},
            {"icon":"",  "label":"Mes Cours",      "href":"/cours"},
            {"icon":"",  "label":"Présences",      "href":"/presences"},
            {"icon":"",  "label":"Mes Étudiants",  "href":"/etudiants"},
        ]),
        ("Outils", [
            {"icon":"", "label":"Appel Rapide",   "href":"/appel"},
            {"icon":"", "label":"Bulletins PDF",  "href":"/bulletin"},
            {"icon":"", "label":"Calendrier",     "href":"/calendrier"},
            {"icon":"",  "label":"Emploi du temps","href":"/emploi-du-temps"},
            {"icon":"", "label":"Alertes",        "href":"/alertes"},
            {"icon":"",  "label":"Messagerie",     "href":"/messagerie"},
        ]),
    ],
    "secretary": [
        ("Navigation", [
            {"icon":"",  "label":"Secretariat",   "href":"/portail-secretaire"},
            {"icon":"",  "label":"Messagerie",    "href":"/messagerie"},
        ]),
    ],
    "student": [
        ("Navigation", [
            {"icon":"",  "label":"Mon espace",    "href":"/portail-etudiant"},
            {"icon":"",  "label":"Emploi du temps","href":"/emploi-du-temps"},
            {"icon":"",  "label":"Messagerie",    "href":"/messagerie"},
        ]),
    ],
    "parent": [
        ("Navigation", [
            {"icon":"",  "label":"Mon espace",    "href":"/portail-parent"},
            {"icon":"",  "label":"Messagerie",    "href":"/messagerie"},
        ]),
    ],
}

def create_sidebar(role="admin", username=""):
    init_db()
    db = SessionLocal()
    try:
        nb_notifs = db.query(Notification).filter_by(lu=False).count()
    except Exception:
        nb_notifs = 0
    finally:
        db.close()

    sections = NAV_BY_ROLE.get(role, NAV_BY_ROLE["teacher"])
    role_label, role_icon = ROLE_LABELS.get(role, ("Utilisateur", "◆"))
    initials = (username[:2].upper() if username else role_icon)

    def nav_link(item):
        badge = (html.Span(str(nb_notifs), className="nav-badge")
                 if item["href"] in ("/", "/alertes") and nb_notifs > 0 else None)
        children = [html.Span(item["icon"], className="nav-icon"), item["label"]]
        if badge: children.append(badge)
        return dcc.Link(children, href=item["href"], className="nav-link-item")

    nav_children = []
    for section_label, items in sections:
        nav_children.append(html.Div(section_label, className="nav-section-label"))
        nav_children.extend([nav_link(i) for i in items])

    # Bouton déconnexion
    nav_children.append(html.Div(style={"flex":"1"}))

    return html.Div([
        html.Div([
            html.H1("SGA PRO"),
            html.P("Système de Gestion Académique"),
        ], className="sidebar-logo"),
        html.Nav(nav_children, className="sidebar-nav",
                 style={"display":"flex","flexDirection":"column","flex":"1"}),
        html.Div([
            html.Div([
                html.Div(initials, className="user-avatar"),
                html.Div([
                    html.Div(username or role_label,
                             style={"color":"var(--text-primary)","fontWeight":"600","fontSize":"13px",
                                    "overflow":"hidden","textOverflow":"ellipsis","whiteSpace":"nowrap","maxWidth":"120px"}),
                    html.Div(role_label,
                             style={"fontSize":"11px","color":"var(--text-muted)"}),
                ]),
                dcc.Link("", href="/auth",
                         style={"marginLeft":"auto","fontSize":"18px","color":"var(--muted)",
                                "textDecoration":"none","transition":"color 0.2s"},
                         title="Déconnexion"),
            ], style={"display":"flex","gap":"10px","alignItems":"center"}),
        ], className="sidebar-footer"),
    ], className="sidebar")
