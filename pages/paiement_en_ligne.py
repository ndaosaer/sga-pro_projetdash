"""
Nafa Scolaire — Module Paiement Paytech
Intègre Wave, Orange Money, Free Money, Carte bancaire
via l'agrégateur Paytech (paytech.sn)
"""
import dash, requests, hashlib, json, os
from dash import html, dcc, Input, Output, State, callback, ctx
from database import SessionLocal
from models import (Student, FraisScolarite, Paiement,
                    Candidat, Concours, User)
from datetime import datetime

dash.register_page(__name__, path="/paiement-en-ligne", name="Paiement en ligne")

# ── Clés Paytech (remplacer par les vraies en production) ──
PAYTECH_API_KEY    = os.environ.get("PAYTECH_API_KEY",    "TEST_API_KEY_SGA_PRO")
PAYTECH_API_SECRET = os.environ.get("PAYTECH_API_SECRET", "TEST_API_SECRET_SGA_PRO")
PAYTECH_ENV        = os.environ.get("PAYTECH_ENV",        "test")  # "test" ou "prod"

PAYTECH_URL = "https://paytech.sn/api/payment/request-payment"
GOLD   = "#B8922A"
DARK   = "#1A1712"


def layout():
    # Recuperer les parametres depuis l'URL (?type=concours&id=X)
    return html.Div([
        dcc.Location(id="pay-url", refresh=False),
        dcc.Store(id="pay-store", data={}),

        html.Div([
            html.Div([
                html.Div("Paiement en ligne", className="page-title"),
                html.Div("Sécurisé par Paytech · Wave · Orange Money · Carte bancaire",
                         className="page-subtitle"),
            ]),
        ], className="topbar"),

        html.Div([
            html.Div([

                # ── Sélecteur de type ──
                html.Div([
                    html.Div("Type de paiement", className="sga-label"),
                    html.Div([
                        _type_btn("concours",    " Frais de concours",   "Candidats au concours d'admission"),
                        _type_btn("inscription", " Frais d'inscription", "Nouveaux etudiants inscrits"),
                        _type_btn("scolarite",   " Frais de scolarite",  "Etudiants — paiement annuel"),
                    ], style={"display":"flex","gap":"12px","flexWrap":"wrap",
                              "marginBottom":"28px"}),
                ]),

                # ── Formulaire dynamique ──
                html.Div(id="pay-form"),

                # ── Confirmation avant paiement ──
                html.Div(id="pay-recap", style={"marginTop":"24px"}),

                # ── Feedback ──
                html.Div(id="pay-feedback", style={"marginTop":"16px"}),

            ], className="sga-card", style={"maxWidth":"640px","margin":"0 auto"}),

            # ── Badges moyens de paiement ──
            html.Div([
                html.Div("Moyens de paiement acceptés", style={
                    "fontSize":"11px","letterSpacing":"2px","textTransform":"uppercase",
                    "color":"var(--muted)","marginBottom":"16px","textAlign":"center"}),
                html.Div([
                    _badge_paiement("", "Orange Money"),
                    _badge_paiement("", "Wave"),
                    _badge_paiement("", "Free Money"),
                    _badge_paiement("", "Carte bancaire"),
                    _badge_paiement("", "Virement"),
                ], style={"display":"flex","gap":"12px","justifyContent":"center",
                          "flexWrap":"wrap"}),
            ], style={"marginTop":"24px","maxWidth":"640px","margin":"24px auto 0"}),

        ], style={"padding":"24px"}),
    ])


def _type_btn(value, label, subtitle):
    return html.Div([
        html.Div(label, style={"fontWeight":"700","fontSize":"13px","marginBottom":"3px"}),
        html.Div(subtitle, style={"fontSize":"10px","color":"var(--muted)"}),
    ], id={"type":"pay-type-btn","index":value},
       n_clicks=0,
       style={"padding":"16px 20px","border":"1px solid var(--border)",
              "borderRadius":"6px","cursor":"pointer","flex":"1","minWidth":"160px",
              "background":"var(--bg-card)","transition":"all 0.2s"})


def _badge_paiement(icon, nom):
    return html.Div([
        html.Span(icon, style={"fontSize":"20px","marginBottom":"4px"}),
        html.Div(nom, style={"fontSize":"10px","letterSpacing":"1px",
                             "color":"var(--muted)"}),
    ], style={"display":"flex","flexDirection":"column","alignItems":"center",
              "padding":"12px 16px","border":"1px solid var(--border)",
              "borderRadius":"6px","background":"var(--bg-card)","minWidth":"90px"})


# ── Afficher le formulaire selon le type ──
@callback(
    Output("pay-form","children"),
    Input({"type":"pay-type-btn","index":dash.ALL},"n_clicks"),
    prevent_initial_call=True,
)
def show_form(n_clicks):
    if not ctx.triggered_id or not isinstance(ctx.triggered_id, dict):
        return html.Div()

    type_pay = ctx.triggered_id["index"]
    db = SessionLocal()
    try:
        if type_pay == "concours":
            con = db.query(Concours).filter_by(actif=True).first()
            montant = con.frais_dossier if con and hasattr(con,"frais_dossier") else 15000
            nom_con = con.nom if con else "Concours d'admission"
            return html.Div([
                html.Div(f"Concours : {nom_con}", style={
                    "fontFamily":"Times New Roman,serif","fontSize":"18px",
                    "fontWeight":"700","marginBottom":"20px","color":"var(--gold)"}),
                _champ("Nom", "pay-nom", "Votre nom de famille"),
                _champ("Prénom", "pay-prenom", "Votre prénom"),
                _champ("Email", "pay-email", "votre@email.com", type="email"),
                _champ("Téléphone", "pay-tel", "77 000 00 00"),
                html.Div([
                    html.Div("Montant", className="sga-label"),
                    html.Div(f"{montant:,} FCFA", style={
                        "fontFamily":"JetBrains Mono,monospace","fontSize":"24px",
                        "fontWeight":"700","color":"var(--gold)","marginBottom":"20px"}),
                ]),
                dcc.Store(id="pay-montant", data=montant),
                dcc.Store(id="pay-type",    data="concours"),
                html.Button("Procéder au paiement →", id="btn-pay-go",
                            n_clicks=0, className="btn-sga btn-gold",
                            style={"width":"100%","padding":"14px","fontSize":"13px",
                                   "marginTop":"8px"}),
            ])

        elif type_pay == "inscription":
            montant = 50000  # frais d'inscription standard
            return html.Div([
                html.Div("Frais d'inscription", style={
                    "fontFamily":"Times New Roman,serif","fontSize":"18px",
                    "fontWeight":"700","marginBottom":"20px","color":"var(--gold)"}),
                _champ("Nom", "pay-nom", "Votre nom de famille"),
                _champ("Prénom", "pay-prenom", "Votre prénom"),
                _champ("Email", "pay-email", "votre@email.com", type="email"),
                _champ("Téléphone", "pay-tel", "77 000 00 00"),
                _champ("Numéro de dossier", "pay-dossier", "N° fourni par l'administration"),
                html.Div([
                    html.Div("Montant inscription", className="sga-label"),
                    html.Div(f"{montant:,} FCFA", style={
                        "fontFamily":"JetBrains Mono,monospace","fontSize":"24px",
                        "fontWeight":"700","color":"var(--gold)","marginBottom":"20px"}),
                ]),
                dcc.Store(id="pay-montant", data=montant),
                dcc.Store(id="pay-type",    data="inscription"),
                html.Button("Procéder au paiement →", id="btn-pay-go",
                            n_clicks=0, className="btn-sga btn-gold",
                            style={"width":"100%","padding":"14px","fontSize":"13px",
                                   "marginTop":"8px"}),
            ])

        else:  # scolarite
            students = db.query(Student).filter_by(actif=True).order_by(Student.nom).all()
            stu_opts = [{"label":f"{s.nom} {s.prenom}","value":s.id} for s in students]
            return html.Div([
                html.Div("Paiement scolarité", style={
                    "fontFamily":"Times New Roman,serif","fontSize":"18px",
                    "fontWeight":"700","marginBottom":"20px","color":"var(--gold)"}),
                html.Div([
                    html.Div("Etudiant", className="sga-label"),
                    dcc.Dropdown(id="pay-etu-select", options=stu_opts,
                                 placeholder="Sélectionner l'étudiant...",
                                 style={"marginBottom":"16px"}),
                ]),
                _champ("Email", "pay-email", "votre@email.com", type="email"),
                _champ("Téléphone", "pay-tel", "77 000 00 00"),
                html.Div(id="pay-scol-montant"),
                dcc.Store(id="pay-montant", data=0),
                dcc.Store(id="pay-type",    data="scolarite"),
                html.Button("Procéder au paiement →", id="btn-pay-go",
                            n_clicks=0, className="btn-sga btn-gold",
                            style={"width":"100%","padding":"14px","fontSize":"13px",
                                   "marginTop":"8px"}),
            ])
    finally:
        db.close()


def _champ(label, id_, placeholder, type="text"):
    return html.Div([
        html.Div(label, className="sga-label"),
        dcc.Input(id=id_, type=type, placeholder=placeholder,
                  className="sga-input",
                  style={"width":"100%","marginBottom":"14px"}),
    ])


# ── Charger montant scolarite selon etudiant ──
@callback(
    Output("pay-scol-montant","children"),
    Output("pay-montant","data", allow_duplicate=True),
    Input("pay-etu-select","value"),
    prevent_initial_call=True,
)
def load_scol_montant(stu_id):
    if not stu_id: return html.Div(), 0
    db = SessionLocal()
    try:
        frais = db.query(FraisScolarite).filter_by(
            student_id=stu_id, annee="2025-2026").first()
        if not frais:
            return html.Div("Aucun frais enregistré pour cet étudiant.",
                            className="sga-alert sga-alert-warning"), 0
        payes = db.query(Paiement).filter_by(
            student_id=stu_id, valide=True).all()
        total_paye = sum(p.montant for p in payes)
        reste = max(0, frais.montant_total - total_paye)
        return html.Div([
            html.Div("Montant restant dû", className="sga-label"),
            html.Div(f"{reste:,.0f} FCFA", style={
                "fontFamily":"JetBrains Mono,monospace","fontSize":"24px",
                "fontWeight":"700","color":"var(--gold)","marginBottom":"20px"}),
            html.Div(f"Total annuel : {frais.montant_total:,.0f} FCFA — "
                     f"Déjà payé : {total_paye:,.0f} FCFA",
                     style={"fontSize":"11px","color":"var(--muted)","marginBottom":"14px"}),
        ]), reste
    finally:
        db.close()


# ── Lancer le paiement Paytech ──
@callback(
    Output("pay-feedback","children"),
    Output("pay-recap","children"),
    Input("btn-pay-go","n_clicks"),
    State("pay-type","data"),
    State("pay-montant","data"),
    State("pay-nom","value"),
    State("pay-prenom","value"),
    State("pay-email","value"),
    State("pay-tel","value"),
    prevent_initial_call=True,
)
def lancer_paiement(n, type_pay, montant, nom, prenom, email, tel):
    if not montant or montant <= 0:
        return html.Div("Montant invalide.", className="sga-alert sga-alert-warning"), html.Div()

    # Champs requis selon type
    if not email or not tel:
        return html.Div("Email et téléphone requis.",
                        className="sga-alert sga-alert-warning"), html.Div()

    if type_pay in ("concours","inscription") and not nom:
        return html.Div("Nom requis.", className="sga-alert sga-alert-warning"), html.Div()

    # Construire la référence unique
    ref = f"SGA-{type_pay.upper()[:3]}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    labels = {
        "concours":    "Frais de dossier concours",
        "inscription": "Frais d'inscription",
        "scolarite":   "Paiement scolarité",
    }

    # Payload Paytech
    payload = {
        "item_name":    labels.get(type_pay, "Paiement Nafa Scolaire"),
        "item_price":   str(int(montant)),
        "currency":     "XOF",
        "ref_command":  ref,
        "command_name": f"Nafa Scolaire — {labels.get(type_pay,'')}",
        "env":          PAYTECH_ENV,
        "ipn_url":      os.environ.get("APP_URL","http://localhost:8050") + "/webhook/paytech",
        "success_url":  os.environ.get("APP_URL","http://localhost:8050") + "/paiement-succes",
        "cancel_url":   os.environ.get("APP_URL","http://localhost:8050") + "/paiement-annule",
        "custom_field": json.dumps({
            "type": type_pay, "nom": nom or "",
            "prenom": prenom or "", "email": email, "tel": tel,
        }),
    }

    headers = {
        "API_KEY":    PAYTECH_API_KEY,
        "API_SECRET": PAYTECH_API_SECRET,
        "Content-Type": "application/json",
    }

    try:
        if PAYTECH_ENV == "test":
            # Mode test — simuler une réponse Paytech
            fake_url = f"https://paytech.sn/payment/checkout/{ref}"
            return html.Div(), _recap_paiement(ref, montant, type_pay, email, fake_url, test=True)

        resp = requests.post(PAYTECH_URL, json=payload, headers=headers, timeout=15)
        data = resp.json()

        if resp.status_code == 200 and data.get("success") == 1:
            redirect_url = data.get("redirect_url") or data.get("token")
            return html.Div(), _recap_paiement(ref, montant, type_pay, email, redirect_url)
        else:
            err = data.get("errors") or data.get("message") or str(data)
            return html.Div(f"Erreur Paytech : {err}",
                            className="sga-alert sga-alert-danger"), html.Div()

    except requests.exceptions.ConnectionError:
        return html.Div("Impossible de joindre Paytech. Vérifiez votre connexion.",
                        className="sga-alert sga-alert-danger"), html.Div()
    except Exception as e:
        return html.Div(f"Erreur : {str(e)}",
                        className="sga-alert sga-alert-danger"), html.Div()


def _recap_paiement(ref, montant, type_pay, email, url, test=False):
    labels = {
        "concours":    "Frais de dossier concours",
        "inscription": "Frais d'inscription",
        "scolarite":   "Paiement scolarité",
    }
    return html.Div([
        html.Div([
            html.Div("✓ Paiement initialisé", style={
                "fontFamily":"Times New Roman,serif","fontSize":"20px",
                "fontWeight":"700","color":"var(--green)","marginBottom":"16px"}),

            html.Div([
                _recap_ligne("Référence", ref),
                _recap_ligne("Type", labels.get(type_pay, type_pay)),
                _recap_ligne("Montant", f"{montant:,.0f} FCFA"),
                _recap_ligne("Email", email),
            ], style={"marginBottom":"20px"}),

            html.Div("Cliquez sur le bouton ci-dessous pour finaliser votre paiement "
                     "via Wave, Orange Money, Free Money ou carte bancaire.",
                     style={"fontSize":"13px","color":"var(--muted)","marginBottom":"20px",
                            "lineHeight":"1.7"}),

            html.A("→ Finaliser le paiement sur Paytech",
                   href=url, target="_blank",
                   style={"display":"block","width":"100%","textAlign":"center",
                          "padding":"16px","background":"var(--gold)","color":"#1A1712",
                          "fontFamily":"JetBrains Mono,monospace","fontSize":"13px",
                          "fontWeight":"700","letterSpacing":"2px","textTransform":"uppercase",
                          "borderRadius":"4px","textDecoration":"none",
                          "boxShadow":"0 4px 20px rgba(184,146,42,0.3)"}),

            html.Div("Un email de confirmation sera envoyé après paiement.",
                     style={"fontSize":"11px","color":"var(--muted)","marginTop":"12px",
                            "textAlign":"center"}),

            html.Div("⚠ MODE TEST — lien simulé, aucun vrai paiement effectué",
                     style={"fontSize":"11px","color":"var(--copper)","marginTop":"8px",
                            "textAlign":"center"}) if test else html.Div(),
        ], style={"padding":"24px","background":"rgba(45,106,63,0.06)",
                  "border":"1px solid rgba(45,106,63,0.2)","borderRadius":"6px"}),
    ])


def _recap_ligne(label, valeur):
    return html.Div([
        html.Span(label + " : ", style={"color":"var(--muted)","fontSize":"12px",
                  "fontFamily":"JetBrains Mono,monospace","marginRight":"8px"}),
        html.Span(valeur, style={"fontWeight":"600","fontSize":"13px"}),
    ], style={"marginBottom":"8px"})
