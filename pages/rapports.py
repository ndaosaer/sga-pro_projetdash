import dash, io, smtplib, os
from dash import html, dcc, Input, Output, State, callback, ctx
from database import SessionLocal
from models import (Student, Course, Session, Grade, Attendance,
                    FraisScolarite, Paiement, Candidat, Concours, Notification)
from datetime import datetime, date
from sqlalchemy import func

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, HRFlowable, PageBreak, KeepTogether)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

dash.register_page(__name__, path="/rapports", name="Rapports")

MOIS_FR = ["Janvier","Fevrier","Mars","Avril","Mai","Juin",
           "Juillet","Aout","Septembre","Octobre","Novembre","Decembre"]
ANNEE   = "2025-2026"

# Couleurs charte SGA Pro
OR      = colors.HexColor("#B8922A")
DARK    = colors.HexColor("#1A1712")
BEIGE   = colors.HexColor("#F5F0E6")
VERT    = colors.HexColor("#2D6A3F")
ROUGE   = colors.HexColor("#8B2500")
CUIVRE  = colors.HexColor("#8B5E3C")
GRIS    = colors.HexColor("#8A8070")
BORDURE = colors.HexColor("#E5E0D8")


def layout():
    today = date.today()
    return html.Div([
        dcc.Download(id="rpt-download"),
        dcc.Store(id="rpt-refresh", data=0),

        html.Div([
            html.Div([
                html.Div("Rapports PDF", className="page-title"),
                html.Div("Generation et envoi des rapports officiels", className="page-subtitle"),
            ]),
        ], className="topbar"),

        html.Div([
            # ── Parametres ──
            html.Div([
                html.Div("Parametres du rapport", className="sga-card-title",
                         style={"marginBottom":"20px"}),

                html.Div([
                    # Periode
                    html.Div([
                        html.Div([
                            html.Div("Mois", className="sga-label"),
                            dcc.Dropdown(id="rpt-mois",
                                         options=[{"label":m,"value":i+1}
                                                  for i,m in enumerate(MOIS_FR)],
                                         value=today.month, clearable=False),
                        ], style={"flex":"1"}),
                        html.Div([
                            html.Div("Annee", className="sga-label"),
                            dcc.Input(id="rpt-annee", type="number",
                                      value=today.year, min=2020, max=2030,
                                      className="sga-input", style={"width":"100%"}),
                        ], style={"flex":"1"}),
                        html.Div([
                            html.Div("Nom de l'etablissement", className="sga-label"),
                            dcc.Input(id="rpt-ecole",
                                      value="ENSAE — Ecole Nationale de la Statistique",
                                      className="sga-input", style={"width":"100%"}),
                        ], style={"flex":"3"}),
                    ], style={"display":"flex","gap":"16px","marginBottom":"20px"}),

                    # Sections
                    html.Div("Sections a inclure", className="sga-label"),
                    html.Div([
                        dcc.Checklist(
                            id="rpt-sections",
                            options=[
                                {"label":"Rapport academique (notes, presences, absences)",
                                 "value":"academique"},
                                {"label":"Rapport financier (paiements, impayes)",
                                 "value":"financier"},
                                {"label":"Rapport concours (candidats, admis)",
                                 "value":"concours"},
                                {"label":"Rapport par enseignant (detail par cours)",
                                 "value":"enseignant"},
                            ],
                            value=["academique","financier","concours","enseignant"],
                            style={"display":"flex","flexDirection":"column","gap":"10px",
                                   "fontSize":"13px","marginBottom":"20px"},
                            inputStyle={"marginRight":"10px","accentColor":"var(--gold)"},
                        ),
                    ]),

                    # Email
                    html.Div([
                        html.Div([
                            html.Div("Email destinataire (direction)", className="sga-label"),
                            dcc.Input(id="rpt-email", type="email",
                                      placeholder="direction@ecole.sn",
                                      className="sga-input", style={"width":"100%"}),
                        ], style={"flex":"2"}),
                        html.Div([
                            html.Div("Serveur SMTP", className="sga-label"),
                            dcc.Input(id="rpt-smtp", value="smtp.gmail.com",
                                      className="sga-input", style={"width":"100%"}),
                        ], style={"flex":"1"}),
                        html.Div([
                            html.Div("Port", className="sga-label"),
                            dcc.Input(id="rpt-port", type="number", value=587,
                                      className="sga-input", style={"width":"100%"}),
                        ], style={"flex":"0.5"}),
                    ], style={"display":"flex","gap":"16px","marginBottom":"14px"}),
                    html.Div([
                        html.Div([
                            html.Div("Email expediteur", className="sga-label"),
                            dcc.Input(id="rpt-from", placeholder="sgapro@ecole.sn",
                                      className="sga-input", style={"width":"100%"}),
                        ], style={"flex":"1"}),
                        html.Div([
                            html.Div("Mot de passe SMTP", className="sga-label"),
                            dcc.Input(id="rpt-pwd", type="password",
                                      placeholder="Mot de passe application",
                                      className="sga-input", style={"width":"100%"}),
                        ], style={"flex":"1"}),
                    ], style={"display":"flex","gap":"16px","marginBottom":"24px"}),

                    html.Div([
                        html.Button("Telecharger le PDF", id="btn-rpt-pdf",
                                    n_clicks=0, className="btn-sga btn-gold",
                                    style={"fontSize":"13px","padding":"12px 28px"}),
                        html.Button("Envoyer par email", id="btn-rpt-email",
                                    n_clicks=0, className="btn-sga",
                                    style={"fontSize":"13px","padding":"12px 28px"}),
                    ], style={"display":"flex","gap":"12px"}),

                    html.Div(id="rpt-feedback", style={"marginTop":"16px"}),
                ]),
            ], className="sga-card", style={"marginBottom":"24px"}),

            # ── Apercu ──
            html.Div([
                html.Div("Apercu du rapport", className="sga-card-title",
                         style={"marginBottom":"16px"}),
                html.Div(id="rpt-apercu"),
            ], className="sga-card"),

        ], style={"padding":"24px"}),
    ])


# ── Apercu dynamique ──
@callback(
    Output("rpt-apercu","children"),
    Input("rpt-mois","value"),
    Input("rpt-annee","value"),
    Input("rpt-sections","value"),
)
def apercu(mois, annee, sections):
    if not mois or not annee:
        return html.Div()
    data = _collecter_donnees(int(mois), int(annee))
    parts = []

    if "academique" in (sections or []):
        parts.append(html.Div([
            html.Div("Academique", style={"fontSize":"10px","letterSpacing":"2px",
                     "textTransform":"uppercase","color":"var(--muted)","marginBottom":"10px"}),
            html.Div([
                _mini_kpi(str(data["nb_etudiants"]),  "Etudiants actifs"),
                _mini_kpi(str(data["nb_cours"]),      "Cours"),
                _mini_kpi(str(data["nb_seances"]),    "Seances ce mois"),
                _mini_kpi(f"{data['avg_global']:.1f}/20", "Moyenne"),
                _mini_kpi(f"{data['taux_abs']:.1f}%", "Taux absence"),
            ], style={"display":"flex","gap":"12px","flexWrap":"wrap"}),
        ], style={"marginBottom":"20px","paddingBottom":"20px","borderBottom":"1px solid var(--border)"}))

    if "financier" in (sections or []) and data.get("fin"):
        f = data["fin"]
        parts.append(html.Div([
            html.Div("Financier", style={"fontSize":"10px","letterSpacing":"2px",
                     "textTransform":"uppercase","color":"var(--muted)","marginBottom":"10px"}),
            html.Div([
                _mini_kpi(f"{f['total_du']:,.0f}", "Total du (FCFA)"),
                _mini_kpi(f"{f['total_paye']:,.0f}", "Encaisse"),
                _mini_kpi(f"{f['taux_rec']:.1f}%", "Recouvrement"),
                _mini_kpi(str(f["nb_retard"]), "En retard"),
            ], style={"display":"flex","gap":"12px","flexWrap":"wrap"}),
        ], style={"marginBottom":"20px","paddingBottom":"20px","borderBottom":"1px solid var(--border)"}))

    if "concours" in (sections or []) and data.get("con"):
        c = data["con"]
        parts.append(html.Div([
            html.Div("Concours", style={"fontSize":"10px","letterSpacing":"2px",
                     "textTransform":"uppercase","color":"var(--muted)","marginBottom":"10px"}),
            html.Div([
                _mini_kpi(str(c["total"]),   "Candidats"),
                _mini_kpi(str(c["admis"]),   "Admis"),
                _mini_kpi(str(c["payes"]),   "Paiements"),
                _mini_kpi(str(c["valides"]), "Dossiers valides"),
            ], style={"display":"flex","gap":"12px","flexWrap":"wrap"}),
        ], style={"marginBottom":"20px"}))

    if not parts:
        return html.Div("Selectionnez au moins une section.", style={"color":"var(--muted)","fontSize":"13px"})

    nom_mois = MOIS_FR[int(mois)-1]
    return html.Div([
        html.Div(f"Rapport — {nom_mois} {annee}",
                 style={"fontFamily":"Times New Roman,serif","fontSize":"20px",
                        "fontWeight":"700","marginBottom":"20px","color":"var(--gold)"}),
        *parts,
    ])


# ── Telecharger PDF ──
@callback(
    Output("rpt-download","data"),
    Output("rpt-feedback","children", allow_duplicate=True),
    Input("btn-rpt-pdf","n_clicks"),
    State("rpt-mois","value"),
    State("rpt-annee","value"),
    State("rpt-ecole","value"),
    State("rpt-sections","value"),
    prevent_initial_call=True,
)
def telecharger(n, mois, annee, ecole, sections):
    if not mois or not annee:
        return dash.no_update, html.Div("Mois et annee requis.",
                                        className="sga-alert sga-alert-warning")
    try:
        pdf_bytes = _generer_pdf(int(mois), int(annee), ecole or "Etablissement", sections or [])
        nom = f"rapport_{MOIS_FR[int(mois)-1]}_{annee}.pdf"
        return dcc.send_bytes(pdf_bytes, nom), html.Div(
            f"PDF genere : {nom}", className="sga-alert sga-alert-success")
    except Exception as e:
        return dash.no_update, html.Div(str(e), className="sga-alert sga-alert-danger")


# ── Envoyer par email ──
@callback(
    Output("rpt-feedback","children"),
    Input("btn-rpt-email","n_clicks"),
    State("rpt-mois","value"),
    State("rpt-annee","value"),
    State("rpt-ecole","value"),
    State("rpt-sections","value"),
    State("rpt-email","value"),
    State("rpt-smtp","value"),
    State("rpt-port","value"),
    State("rpt-from","value"),
    State("rpt-pwd","value"),
    prevent_initial_call=True,
)
def envoyer_email(n, mois, annee, ecole, sections, dest, smtp, port, from_addr, pwd):
    if not dest:
        return html.Div("Email destinataire requis.", className="sga-alert sga-alert-warning")
    if not from_addr or not pwd:
        return html.Div("Email expediteur et mot de passe SMTP requis.",
                        className="sga-alert sga-alert-warning")
    try:
        import ssl
        from email.mime.multipart import MIMEMultipart
        from email.mime.base import MIMEBase
        from email.mime.text import MIMEText
        from email import encoders

        pdf_bytes = _generer_pdf(int(mois), int(annee), ecole or "Etablissement", sections or [])
        nom_mois  = MOIS_FR[int(mois)-1]
        nom_pdf   = f"rapport_{nom_mois}_{annee}.pdf"

        msg = MIMEMultipart()
        msg["From"]    = from_addr
        msg["To"]      = dest
        msg["Subject"] = f"SGA Pro — Rapport mensuel {nom_mois} {annee}"
        msg.attach(MIMEText(
            f"Bonjour,\n\nVeuillez trouver ci-joint le rapport mensuel de {nom_mois} {annee} "
            f"genere par SGA Pro.\n\nCordialement,\nSGA Pro", "plain"))

        part = MIMEBase("application", "octet-stream")
        part.set_payload(pdf_bytes)
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{nom_pdf}"')
        msg.attach(part)

        ctx_ssl = ssl.create_default_context()
        with smtplib.SMTP(smtp or "smtp.gmail.com", int(port or 587)) as server:
            server.ehlo()
            server.starttls(context=ctx_ssl)
            server.login(from_addr, pwd)
            server.sendmail(from_addr, dest, msg.as_string())

        return html.Div(f"Rapport envoye a {dest}.", className="sga-alert sga-alert-success")
    except Exception as e:
        return html.Div(f"Erreur envoi : {e}", className="sga-alert sga-alert-danger")


# ═══════════════════════════════════════════════
# COLLECTE DES DONNEES
# ═══════════════════════════════════════════════
def _collecter_donnees(mois, annee):
    db = SessionLocal()
    try:
        d = {}
        students  = db.query(Student).filter_by(actif=True).all()
        courses   = db.query(Course).all()
        grades    = db.query(Grade).all()
        d["nb_etudiants"] = len(students)
        d["nb_cours"]     = len(courses)

        # Seances du mois
        seances_mois = [s for s in db.query(Session).all()
                        if s.date and s.date.month == mois and s.date.year == annee]
        d["nb_seances"] = len(seances_mois)

        # Moyenne globale
        notes = [g.note for g in grades]
        d["avg_global"] = sum(notes)/len(notes) if notes else 0

        # Absences du mois
        att_mois = []
        for s in seances_mois:
            att_mois.extend(db.query(Attendance).filter_by(id_session=s.id).all())
        total_presences = len(seances_mois) * max(1, len(students))
        d["taux_abs"] = len(att_mois) / total_presences * 100 if total_presences else 0
        d["nb_absences"] = len(att_mois)

        # Par etudiant
        etudiants_data = []
        for s in students:
            gs  = [g for g in grades if g.id_student == s.id]
            tc  = sum(g.coefficient for g in gs)
            moy = sum(g.note * g.coefficient for g in gs)/tc if tc and gs else None
            abs_etu = sum(1 for a in att_mois if a.id_student == s.id)
            etudiants_data.append({
                "nom":      f"{s.nom} {s.prenom}",
                "email":    s.email or "",
                "moyenne":  moy,
                "absences": abs_etu,
            })
        etudiants_data.sort(key=lambda x: (x["moyenne"] or 0), reverse=True)
        d["etudiants"] = etudiants_data

        # Par cours
        cours_data = []
        for c in courses:
            gs  = [g for g in grades if g.course_code == c.code]
            tc  = sum(g.coefficient for g in gs)
            moy = sum(g.note * g.coefficient for g in gs)/tc if tc and gs else None
            nb_s = sum(1 for s in seances_mois if s.course_code == c.code)
            cours_data.append({
                "code":      c.code,
                "libelle":   c.libelle,
                "enseignant":c.enseignant or c.teacher_username or "—",
                "moyenne":   moy,
                "seances":   nb_s,
            })
        d["cours"] = sorted(cours_data, key=lambda x: x["libelle"])

        # Financier
        try:
            frais_all = db.query(FraisScolarite).filter_by(annee=ANNEE).all()
            pays_all  = db.query(Paiement).filter_by(valide=True).all()
            total_du  = sum(f.montant_total for f in frais_all)
            total_paye = sum(p.montant for p in pays_all)
            nb_a_jour = sum(1 for f in frais_all
                            if sum(p.montant for p in pays_all if p.student_id==f.student_id) >= f.montant_total)
            # Paiements du mois
            pays_mois = [p for p in pays_all
                         if p.date_paiement and p.date_paiement.month == mois
                         and p.date_paiement.year == annee]
            d["fin"] = {
                "total_du":    total_du,
                "total_paye":  total_paye,
                "total_reste": max(0, total_du - total_paye),
                "taux_rec":    total_paye/total_du*100 if total_du else 0,
                "nb_a_jour":   nb_a_jour,
                "nb_retard":   len(frais_all) - nb_a_jour,
                "pays_mois":   sum(p.montant for p in pays_mois),
                "nb_pays_mois":len(pays_mois),
                "impayes":     [{
                    "nom":   next((f"{s.nom} {s.prenom}" for s in students if s.id==f.student_id), "—"),
                    "reste": f.montant_total - sum(p.montant for p in pays_all if p.student_id==f.student_id),
                } for f in frais_all
                  if sum(p.montant for p in pays_all if p.student_id==f.student_id) < f.montant_total],
            }
        except Exception:
            d["fin"] = None

        # Concours
        try:
            con = db.query(Concours).filter_by(actif=True).order_by(Concours.annee.desc()).first()
            if con:
                cands = db.query(Candidat).filter_by(concours_id=con.id).all()
                d["con"] = {
                    "nom":     con.nom,
                    "annee":   con.annee,
                    "total":   len(cands),
                    "admis":   sum(1 for c in cands if c.admis),
                    "valides": sum(1 for c in cands if c.statut == "valide"),
                    "payes":   sum(1 for c in cands if c.paiement_statut in ("paye","simule")),
                    "rejetes": sum(1 for c in cands if c.statut == "rejete"),
                }
            else:
                d["con"] = None
        except Exception:
            d["con"] = None

        return d
    finally:
        db.close()


# ═══════════════════════════════════════════════
# GENERATION PDF
# ═══════════════════════════════════════════════
def _generer_pdf(mois, annee, ecole, sections):
    data     = _collecter_donnees(mois, annee)
    nom_mois = MOIS_FR[mois - 1]
    buf      = io.BytesIO()

    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    styles  = getSampleStyleSheet()
    s_title = ParagraphStyle("s_title", fontSize=28, textColor=OR,
                              fontName="Times-Bold", alignment=TA_CENTER, spaceAfter=6)
    s_sub   = ParagraphStyle("s_sub",   fontSize=13, textColor=GRIS,
                              fontName="Times-Italic", alignment=TA_CENTER, spaceAfter=4)
    s_h1    = ParagraphStyle("s_h1",    fontSize=16, textColor=DARK,
                              fontName="Times-Bold", spaceBefore=18, spaceAfter=8,
                              borderPad=4)
    s_h2    = ParagraphStyle("s_h2",    fontSize=12, textColor=OR,
                              fontName="Helvetica-Bold", spaceBefore=12, spaceAfter=6)
    s_body  = ParagraphStyle("s_body",  fontSize=10, textColor=DARK,
                              fontName="Helvetica", spaceAfter=4, leading=14)
    s_small = ParagraphStyle("s_small", fontSize=8, textColor=GRIS,
                              fontName="Helvetica", alignment=TA_RIGHT)

    elems = []

    # ── PAGE DE GARDE ──
    elems += [
        Spacer(1, 3*cm),
        Paragraph("SGA PRO", s_title),
        Paragraph("Systeme de Gestion Academique", s_sub),
        Spacer(1, 0.5*cm),
        HRFlowable(width="100%", thickness=2, color=OR, spaceAfter=0.5*cm),
        Paragraph(f"Rapport Mensuel", ParagraphStyle("rpt", fontSize=22, textColor=DARK,
                  fontName="Times-Bold", alignment=TA_CENTER, spaceAfter=8)),
        Paragraph(f"{nom_mois} {annee}", ParagraphStyle("periode", fontSize=18, textColor=OR,
                  fontName="Times-Italic", alignment=TA_CENTER, spaceAfter=16)),
        HRFlowable(width="100%", thickness=1, color=BORDURE, spaceAfter=1*cm),
        Paragraph(ecole, ParagraphStyle("ecole", fontSize=14, textColor=GRIS,
                  fontName="Helvetica", alignment=TA_CENTER, spaceAfter=8)),
        Paragraph(f"Genere le {date.today().strftime('%d/%m/%Y')} par SGA Pro",
                  ParagraphStyle("gen", fontSize=10, textColor=GRIS,
                  fontName="Helvetica", alignment=TA_CENTER)),
        Spacer(1, 2*cm),
    ]

    # Sommaire
    sommaire_items = []
    if "academique" in sections: sommaire_items.append("1. Situation academique")
    if "financier"  in sections: sommaire_items.append("2. Situation financiere")
    if "concours"   in sections: sommaire_items.append("3. Module concours")
    if "enseignant" in sections: sommaire_items.append("4. Rapport par cours")

    if sommaire_items:
        elems.append(Paragraph("Sommaire", s_h2))
        for item in sommaire_items:
            elems.append(Paragraph(item, s_body))

    elems.append(PageBreak())

    # ── SECTION ACADEMIQUE ──
    if "academique" in sections:
        elems += [
            Paragraph("1. Situation Academique", s_h1),
            HRFlowable(width="100%", thickness=1, color=OR, spaceAfter=0.4*cm),
        ]

        # KPIs
        kpi_data = [
            ["Etudiants actifs", str(data["nb_etudiants"]),
             "Cours au programme", str(data["nb_cours"])],
            ["Seances ce mois", str(data["nb_seances"]),
             "Moyenne generale", f"{data['avg_global']:.2f}/20"],
            ["Absences ce mois", str(data["nb_absences"]),
             "Taux d'absence", f"{data['taux_abs']:.1f}%"],
        ]
        t_kpi = Table(kpi_data, colWidths=[4*cm, 3*cm, 4*cm, 3*cm])
        t_kpi.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (0,-1), BEIGE),
            ("BACKGROUND",  (2,0), (2,-1), BEIGE),
            ("FONTNAME",    (1,0), (1,-1), "Helvetica-Bold"),
            ("FONTNAME",    (3,0), (3,-1), "Helvetica-Bold"),
            ("FONTSIZE",    (1,0), (1,-1), 14),
            ("FONTSIZE",    (3,0), (3,-1), 14),
            ("TEXTCOLOR",   (1,0), (1,-1), OR),
            ("TEXTCOLOR",   (3,0), (3,-1), OR),
            ("FONTSIZE",    (0,0), (-1,-1), 10),
            ("GRID",        (0,0), (-1,-1), 0.5, BORDURE),
            ("PADDING",     (0,0), (-1,-1), 8),
            ("ALIGN",       (1,0), (1,-1), "CENTER"),
            ("ALIGN",       (3,0), (3,-1), "CENTER"),
        ]))
        elems += [t_kpi, Spacer(1, 0.5*cm)]

        # Tableau etudiants
        elems.append(Paragraph("Classement des etudiants", s_h2))
        etu_rows = [["#", "Nom & Prenom", "Email", "Moyenne /20", "Absences"]]
        for i, e in enumerate(data["etudiants"], 1):
            moy_str = f"{e['moyenne']:.2f}" if e["moyenne"] is not None else "—"
            etu_rows.append([str(i), e["nom"], e["email"], moy_str, str(e["absences"])])
        t_etu = Table(etu_rows, colWidths=[0.8*cm, 4.5*cm, 5*cm, 2.5*cm, 2*cm])
        _style_table(t_etu, len(etu_rows))
        elems += [t_etu, Spacer(1, 0.3*cm)]

        # Tableau cours
        elems.append(Paragraph("Bilan par cours", s_h2))
        cours_rows = [["Code", "Matiere", "Enseignant", "Seances", "Moyenne"]]
        for c in data["cours"]:
            moy_str = f"{c['moyenne']:.2f}" if c["moyenne"] is not None else "—"
            cours_rows.append([c["code"], c["libelle"], c["enseignant"],
                               str(c["seances"]), moy_str])
        t_cours = Table(cours_rows, colWidths=[1.5*cm, 5.5*cm, 4*cm, 2*cm, 2*cm])
        _style_table(t_cours, len(cours_rows))
        elems += [t_cours, PageBreak()]

    # ── SECTION FINANCIERE ──
    if "financier" in sections and data.get("fin"):
        f = data["fin"]
        elems += [
            Paragraph("2. Situation Financiere", s_h1),
            HRFlowable(width="100%", thickness=1, color=OR, spaceAfter=0.4*cm),
        ]

        kpi_fin = [
            ["Total du (FCFA)", f"{f['total_du']:,.0f}",
             "Total encaisse", f"{f['total_paye']:,.0f}"],
            ["Reste a percevoir", f"{f['total_reste']:,.0f}",
             "Taux de recouvrement", f"{f['taux_rec']:.1f}%"],
            ["Etudiants a jour", str(f["nb_a_jour"]),
             "En retard de paiement", str(f["nb_retard"])],
            [f"Encaisse en {MOIS_FR[mois-1]}", f"{f['pays_mois']:,.0f} FCFA",
             "Nb paiements ce mois", str(f["nb_pays_mois"])],
        ]
        t_fin = Table(kpi_fin, colWidths=[4*cm, 3.5*cm, 4*cm, 3.5*cm])
        t_fin.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (0,-1), BEIGE),
            ("BACKGROUND",  (2,0), (2,-1), BEIGE),
            ("FONTNAME",    (1,0), (1,-1), "Helvetica-Bold"),
            ("FONTNAME",    (3,0), (3,-1), "Helvetica-Bold"),
            ("FONTSIZE",    (1,0), (1,-1), 13),
            ("FONTSIZE",    (3,0), (3,-1), 13),
            ("TEXTCOLOR",   (1,0), (1,-1), VERT),
            ("TEXTCOLOR",   (3,0), (3,-1), CUIVRE),
            ("FONTSIZE",    (0,0), (-1,-1), 10),
            ("GRID",        (0,0), (-1,-1), 0.5, BORDURE),
            ("PADDING",     (0,0), (-1,-1), 8),
            ("ALIGN",       (1,0), (1,-1), "CENTER"),
            ("ALIGN",       (3,0), (3,-1), "CENTER"),
        ]))
        elems += [t_fin, Spacer(1, 0.5*cm)]

        # Impayes
        if f["impayes"]:
            elems.append(Paragraph("Etudiants en impaye", s_h2))
            imp_rows = [["Etudiant", "Reste du (FCFA)"]]
            for imp in sorted(f["impayes"], key=lambda x: x["reste"], reverse=True):
                imp_rows.append([imp["nom"], f"{imp['reste']:,.0f}"])
            t_imp = Table(imp_rows, colWidths=[10*cm, 5*cm])
            _style_table(t_imp, len(imp_rows))
            elems.append(t_imp)
        elems.append(PageBreak())

    # ── SECTION CONCOURS ──
    if "concours" in sections and data.get("con"):
        c = data["con"]
        elems += [
            Paragraph("3. Module Concours", s_h1),
            HRFlowable(width="100%", thickness=1, color=OR, spaceAfter=0.4*cm),
            Paragraph(f"{c['nom']} — {c['annee']}", s_h2),
        ]
        con_data = [
            ["Candidats inscrits", str(c["total"]),
             "Paiements recus", str(c["payes"])],
            ["Dossiers valides", str(c["valides"]),
             "Candidats admis", str(c["admis"])],
            ["Dossiers rejetes", str(c["rejetes"]),
             "Taux d'admission",
             f"{c['admis']/max(1,c['total'])*100:.1f}%"],
        ]
        t_con = Table(con_data, colWidths=[4*cm, 3*cm, 4*cm, 3*cm])
        t_con.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (0,-1), BEIGE),
            ("BACKGROUND",  (2,0), (2,-1), BEIGE),
            ("FONTNAME",    (1,0), (1,-1), "Helvetica-Bold"),
            ("FONTNAME",    (3,0), (3,-1), "Helvetica-Bold"),
            ("FONTSIZE",    (1,0), (1,-1), 14),
            ("FONTSIZE",    (3,0), (3,-1), 14),
            ("TEXTCOLOR",   (1,0), (1,-1), OR),
            ("TEXTCOLOR",   (3,0), (3,-1), VERT),
            ("FONTSIZE",    (0,0), (-1,-1), 10),
            ("GRID",        (0,0), (-1,-1), 0.5, BORDURE),
            ("PADDING",     (0,0), (-1,-1), 8),
            ("ALIGN",       (1,0), (1,-1), "CENTER"),
            ("ALIGN",       (3,0), (3,-1), "CENTER"),
        ]))
        elems += [t_con, PageBreak()]

    # ── SECTION PAR ENSEIGNANT ──
    if "enseignant" in sections:
        elems += [
            Paragraph("4. Rapport par Cours", s_h1),
            HRFlowable(width="100%", thickness=1, color=OR, spaceAfter=0.4*cm),
        ]
        db = SessionLocal()
        try:
            grades_all = db.query(Grade).all()
            courses_all = db.query(Course).all()
            students_all = db.query(Student).all()
            stu_map = {s.id: s for s in students_all}

            for course in sorted(courses_all, key=lambda x: x.libelle):
                gs = [g for g in grades_all if g.course_code == course.code]
                if not gs:
                    continue
                tc  = sum(g.coefficient for g in gs)
                moy = sum(g.note * g.coefficient for g in gs)/tc if tc else 0

                rows = [["Etudiant", "Note /20", "Coefficient", "Mention"]]
                for g in sorted(gs, key=lambda x: x.note, reverse=True):
                    stu = stu_map.get(g.id_student)
                    nom = f"{stu.nom} {stu.prenom}" if stu else str(g.id_student)
                    mention = ("TB" if g.note >= 16 else "B" if g.note >= 14
                               else "AB" if g.note >= 12 else "P" if g.note >= 10 else "I")
                    rows.append([nom, f"{g.note:.2f}", str(g.coefficient), mention])

                ens = course.enseignant or course.teacher_username or "—"
                bloc = [
                    Paragraph(f"{course.code} — {course.libelle}", s_h2),
                    Paragraph(f"Enseignant : {ens}   |   Moyenne : {moy:.2f}/20   |   {len(gs)} note(s)",
                              s_small),
                    Spacer(1, 0.2*cm),
                ]
                t = Table(rows, colWidths=[7*cm, 3*cm, 3*cm, 2*cm])
                _style_table(t, len(rows))
                bloc += [t, Spacer(1, 0.4*cm)]
                elems.append(KeepTogether(bloc))
        finally:
            db.close()

    # ── PIED DE PAGE ──
    elems += [
        Spacer(1, 1*cm),
        HRFlowable(width="100%", thickness=1, color=BORDURE),
        Paragraph(f"SGA Pro — {ecole} — Rapport {nom_mois} {annee} — Confidentiel",
                  ParagraphStyle("footer", fontSize=8, textColor=GRIS,
                  fontName="Helvetica", alignment=TA_CENTER, spaceBefore=8)),
    ]

    doc.build(elems)
    buf.seek(0)
    return buf.read()


def _style_table(t, nb_rows):
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,0),  DARK),
        ("TEXTCOLOR",   (0,0), (-1,0),  OR),
        ("FONTNAME",    (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, BEIGE]),
        ("GRID",        (0,0), (-1,-1), 0.5, BORDURE),
        ("PADDING",     (0,0), (-1,-1), 6),
        ("ALIGN",       (0,0), (-1,-1), "LEFT"),
        ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
    ]))


def _mini_kpi(val, label):
    return html.Div([
        html.Div(val, style={"fontFamily":"JetBrains Mono,monospace","fontSize":"20px",
                             "fontWeight":"700","color":"var(--gold)"}),
        html.Div(label, style={"fontSize":"10px","color":"var(--muted)","letterSpacing":"1px"}),
    ], style={"padding":"12px 16px","background":"var(--bg-secondary)",
              "borderRadius":"4px","minWidth":"120px"})
