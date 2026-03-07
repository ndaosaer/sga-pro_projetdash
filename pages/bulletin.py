import dash
from dash import html, dcc, Input, Output, State, callback
from database import SessionLocal
from models import Student, Course, Grade, Attendance, Session
from datetime import date
import io, base64

dash.register_page(__name__, path="/bulletin", name="Bulletins PDF")

def layout():
    db = SessionLocal()
    students = [(s.id, f"{s.nom} {s.prenom}")
                for s in db.query(Student).filter_by(actif=True).order_by(Student.nom).all()]
    db.close()
    opts = [{"label": n, "value": sid} for sid, n in students]

    return html.Div([
        html.Div([
            html.Div([
                html.Div("Bulletins de Notes", className="page-title"),
                html.Div("Génération PDF individuelle ou collective", className="page-subtitle"),
            ]),
        ], className="topbar"),

        html.Div([
            # Panneau gauche — sélection
            html.Div([
                html.Div([
                    html.Div("Générer un bulletin", className="sga-card-title",
                             style={"marginBottom":"20px"}),
                    html.Div([
                        html.Span("Étudiant", className="sga-label"),
                        dcc.Dropdown(id="bull-stu", options=opts,
                                     placeholder="Sélectionner un étudiant…",
                                     clearable=False),
                    ], style={"marginBottom":"16px"}),
                    html.Div([
                        html.Span("Période / Semestre", className="sga-label"),
                        dcc.Input(id="bull-periode", value="Semestre 1 — 2025/2026",
                                  className="sga-input", style={"width":"100%"}),
                    ], style={"marginBottom":"16px"}),
                    html.Div([
                        html.Span("Appréciation générale (optionnel)", className="sga-label"),
                        dcc.Textarea(id="bull-appre",
                                     placeholder="Élève sérieux, bon travail…",
                                     style={"width":"100%","height":"80px",
                                            "background":"var(--bg-primary)",
                                            "border":"1px solid var(--border)",
                                            "borderRadius":"3px","color":"var(--text-primary)",
                                            "fontFamily":"Times New Roman,serif",
                                            "fontSize":"14px","padding":"10px",
                                            "resize":"vertical"}),
                    ], style={"marginBottom":"20px"}),
                    html.Button(" Générer le bulletin PDF", id="btn-gen-bull",
                                className="btn-sga btn-gold",
                                style={"width":"100%","justifyContent":"center",
                                       "fontSize":"13px","padding":"14px"}),
                    dcc.Download(id="dl-bulletin"),
                    html.Div(id="bull-feedback", style={"marginTop":"12px"}),
                ], className="sga-card"),

                # Génération collective
                html.Div([
                    html.Div("Tous les bulletins", className="sga-card-title",
                             style={"marginBottom":"16px"}),
                    html.Div("Génère un fichier ZIP avec les bulletins de tous les étudiants.",
                             style={"color":"var(--muted)","fontSize":"13px","marginBottom":"16px"}),
                    html.Button(" Générer tous les bulletins", id="btn-gen-all",
                                className="btn-sga btn-green",
                                style={"width":"100%","justifyContent":"center","fontSize":"13px"}),
                    dcc.Download(id="dl-all-bulletins"),
                    html.Div(id="bull-all-feedback", style={"marginTop":"12px"}),
                ], className="sga-card", style={"marginTop":"20px"}),
            ], style={"width":"320px","flexShrink":"0"}),

            # Panneau droit — aperçu
            html.Div([
                html.Div([
                    html.Div("Aperçu du bulletin", className="sga-card-title",
                             style={"marginBottom":"16px"}),
                    html.Div(id="bull-preview",
                             style={"minHeight":"400px"}),
                ], className="sga-card"),
            ], style={"flex":"1"}),
        ], style={"display":"flex","gap":"24px","alignItems":"flex-start"}),
    ])


def _get_donnees_etudiant(sid):
    """Récupère toutes les données nécessaires pour le bulletin."""
    db = SessionLocal()
    try:
        s = db.get(Student, sid)
        if not s:
            return None
        grades      = db.query(Grade).filter_by(id_student=sid).all()
        courses     = db.query(Course).all()
        sessions    = db.query(Session).all()
        attendances = db.query(Attendance).filter_by(id_student=sid).all()

        cours_data = []
        for c in courses:
            g = [gr for gr in grades if gr.course_code == c.code]
            if not g:
                continue
            tc  = sum(gr.coefficient for gr in g)
            moy = round(sum(gr.note * gr.coefficient for gr in g) / tc, 2)
            sess_ids = {se.id for se in sessions if se.course_code == c.code}
            nb_abs   = sum(1 for a in attendances if a.id_session in sess_ids)
            nb_sess  = len(sess_ids)
            taux_abs = round(nb_abs / nb_sess * 100, 1) if nb_sess else 0
            mention  = ("Très Bien" if moy >= 16 else "Bien" if moy >= 14
                        else "Assez Bien" if moy >= 12 else "Passable" if moy >= 10
                        else "Insuffisant")
            cours_data.append({
                "code": c.code, "libelle": c.libelle,
                "enseignant": c.enseignant or "—",
                "note": moy, "coef": tc,
                "mention": mention, "nb_abs": nb_abs,
                "nb_sess": nb_sess, "taux_abs": taux_abs,
            })

        all_grades = []
        for cd in cours_data:
            all_grades.append((cd["note"], cd["coef"]))
        tot_coef = sum(c for _, c in all_grades)
        moy_gen  = round(sum(n * c for n, c in all_grades) / tot_coef, 2) if tot_coef else 0
        rang     = None  # calcul rang optionnel

        return {
            "id": s.id, "nom": s.nom, "prenom": s.prenom,
            "email": s.email,
            "dob": s.date_naissance.strftime("%d/%m/%Y") if s.date_naissance else "—",
            "cours": cours_data, "moy_gen": moy_gen,
        }
    finally:
        db.close()


def _generer_pdf(data, periode, appre):
    """Génère le PDF en bytes via reportlab."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                        Paragraph, Spacer, HRFlowable)
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4,
                                topMargin=1.5*cm, bottomMargin=1.5*cm,
                                leftMargin=2*cm, rightMargin=2*cm)

        # Couleurs
        OR      = colors.HexColor("#B8922A")
        ENCRE   = colors.HexColor("#1E1A12")
        PARCH   = colors.HexColor("#F5F0E6")
        CARD    = colors.HexColor("#FAF7F2")
        MUTED   = colors.HexColor("#8A8070")
        DANGER  = colors.HexColor("#8B2500")
        GREEN   = colors.HexColor("#2D6A3F")

        styles = getSampleStyleSheet()
        def style(name, **kw):
            s = ParagraphStyle(name, **kw)
            return s

        S_titre   = style("titre",   fontName="Times-Bold",   fontSize=28,
                          textColor=OR,    alignment=TA_CENTER, spaceAfter=4)
        S_sub     = style("sub",     fontName="Times-Roman",  fontSize=10,
                          textColor=MUTED, alignment=TA_CENTER, spaceAfter=2,
                          letterSpacing=3)
        S_etud    = style("etud",    fontName="Times-Bold",   fontSize=16,
                          textColor=ENCRE, alignment=TA_CENTER, spaceAfter=2)
        S_info    = style("info",    fontName="Helvetica",    fontSize=9,
                          textColor=MUTED, alignment=TA_CENTER, spaceAfter=12)
        S_appre   = style("appre",   fontName="Times-Italic", fontSize=11,
                          textColor=ENCRE, leading=16)
        S_section = style("section", fontName="Times-Bold",   fontSize=10,
                          textColor=MUTED, letterSpacing=3, spaceAfter=6)
        S_cell    = style("cell",    fontName="Times-Roman",  fontSize=10,
                          textColor=ENCRE)
        S_moy     = style("moy",     fontName="Times-Bold",   fontSize=22,
                          textColor=OR,    alignment=TA_CENTER)
        S_mention = style("mention", fontName="Times-Italic", fontSize=13,
                          textColor=ENCRE, alignment=TA_CENTER)

        elems = []

        # ── EN-TÊTE ──────────────────────────────────────────────────────────
        elems.append(Paragraph("SGA PRO", S_titre))
        elems.append(Paragraph("SYSTÈME DE GESTION ACADÉMIQUE", S_sub))
        elems.append(HRFlowable(width="100%", thickness=0.5,
                                color=OR, spaceAfter=12))

        elems.append(Paragraph("BULLETIN DE NOTES", style("bt", fontName="Times-Bold",
                     fontSize=13, textColor=ENCRE, alignment=TA_CENTER,
                     letterSpacing=5, spaceAfter=4)))
        elems.append(Paragraph(periode, style("per", fontName="Times-Roman",
                     fontSize=10, textColor=MUTED, alignment=TA_CENTER, spaceAfter=16)))

        # ── IDENTITÉ ─────────────────────────────────────────────────────────
        elems.append(Paragraph(f"{data['prenom']} {data['nom']}", S_etud))
        elems.append(Paragraph(
            f"Email : {data['email']}   ·   Date de naissance : {data['dob']}   ·   "
            f"Édité le {date.today().strftime('%d/%m/%Y')}",
            S_info))
        elems.append(HRFlowable(width="100%", thickness=0.3,
                                color=colors.HexColor("#E0D8C8"), spaceAfter=16))

        # ── TABLEAU DES NOTES ────────────────────────────────────────────────
        elems.append(Paragraph("RÉSULTATS PAR MATIÈRE", S_section))

        headers = ["Matière", "Enseignant", "Note /20", "Coef.", "Mention", "Absences"]
        rows = [headers]
        for cd in data["cours"]:
            note_txt  = f"{cd['note']:.2f}"
            abs_txt   = f"{cd['nb_abs']}/{cd['nb_sess']} ({cd['taux_abs']}%)"
            rows.append([
                cd["libelle"][:30], cd["enseignant"][:20],
                note_txt, str(int(cd["coef"])),
                cd["mention"], abs_txt,
            ])

        col_w = [5.5*cm, 3.5*cm, 2.2*cm, 1.5*cm, 2.8*cm, 3.5*cm]
        t = Table(rows, colWidths=col_w, repeatRows=1)

        # Couleur mention
        ts = [
            ("BACKGROUND",  (0,0), (-1,0),  OR),
            ("TEXTCOLOR",   (0,0), (-1,0),  colors.white),
            ("FONTNAME",    (0,0), (-1,0),  "Helvetica-Bold"),
            ("FONTSIZE",    (0,0), (-1,0),  8),
            ("LETTERSPACE", (0,0), (-1,0),  2),
            ("ALIGN",       (0,0), (-1,-1), "CENTER"),
            ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
            ("FONTNAME",    (0,1), (-1,-1), "Times-Roman"),
            ("FONTSIZE",    (0,1), (-1,-1), 10),
            ("ROWBACKGROUNDS",(0,1),(-1,-1), [CARD, PARCH]),
            ("GRID",        (0,0), (-1,-1), 0.3, colors.HexColor("#D8CEB8")),
            ("TOPPADDING",  (0,0), (-1,-1), 7),
            ("BOTTOMPADDING",(0,0),(-1,-1), 7),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
        ]
        # Colorier les notes insuffisantes
        for i, cd in enumerate(data["cours"], 1):
            if cd["note"] < 10:
                ts.append(("TEXTCOLOR", (2,i), (2,i), DANGER))
                ts.append(("FONTNAME",  (2,i), (2,i), "Times-Bold"))
            elif cd["note"] >= 14:
                ts.append(("TEXTCOLOR", (2,i), (2,i), GREEN))
                ts.append(("FONTNAME",  (2,i), (2,i), "Times-Bold"))
            if cd["taux_abs"] > 20:
                ts.append(("TEXTCOLOR", (5,i), (5,i), DANGER))

        t.setStyle(TableStyle(ts))
        elems.append(t)
        elems.append(Spacer(1, 20))

        # ── MOYENNE GÉNÉRALE ─────────────────────────────────────────────────
        moy = data["moy_gen"]
        mention_gen = ("Très Bien" if moy >= 16 else "Bien" if moy >= 14
                       else "Assez Bien" if moy >= 12 else "Passable" if moy >= 10
                       else "Insuffisant")
        moy_color = GREEN if moy >= 12 else (DANGER if moy < 10 else OR)

        moy_table = Table([[
            Paragraph("MOYENNE GÉNÉRALE", style("mg", fontName="Helvetica-Bold",
                      fontSize=8, textColor=MUTED, letterSpacing=2)),
            Paragraph(f"{moy:.2f} / 20", style("mv", fontName="Times-Bold",
                      fontSize=22, textColor=moy_color, alignment=TA_CENTER)),
            Paragraph(mention_gen, style("mm", fontName="Times-Italic",
                      fontSize=13, textColor=ENCRE, alignment=TA_CENTER)),
        ]], colWidths=[5*cm, 5*cm, 9*cm])
        moy_table.setStyle(TableStyle([
            ("BACKGROUND",   (0,0), (-1,-1), CARD),
            ("BOX",          (0,0), (-1,-1), 1, OR),
            ("ALIGN",        (0,0), (-1,-1), "CENTER"),
            ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
            ("TOPPADDING",   (0,0), (-1,-1), 14),
            ("BOTTOMPADDING",(0,0), (-1,-1), 14),
            ("LINEAFTER",    (0,0), (1,-1),  0.5, colors.HexColor("#D8CEB8")),
        ]))
        elems.append(moy_table)
        elems.append(Spacer(1, 20))

        # ── APPRÉCIATION ─────────────────────────────────────────────────────
        if appre and appre.strip():
            elems.append(Paragraph("APPRÉCIATION GÉNÉRALE", S_section))
            elems.append(Paragraph(appre.strip(), S_appre))
            elems.append(Spacer(1, 16))

        # ── PIED DE PAGE ─────────────────────────────────────────────────────
        elems.append(HRFlowable(width="100%", thickness=0.5,
                                color=OR, spaceBefore=20, spaceAfter=8))
        elems.append(Paragraph(
            f"Document généré automatiquement par SGA Pro · {date.today().strftime('%d/%m/%Y')}",
            style("footer", fontName="Helvetica", fontSize=8,
                  textColor=MUTED, alignment=TA_CENTER)))

        doc.build(elems)
        return buf.getvalue()

    except ImportError:
        return None


# ── APERÇU HTML ───────────────────────────────────────────────────────────────
@callback(
    Output("bull-preview", "children"),
    Input("bull-stu", "value"),
    Input("bull-periode", "value"),
    prevent_initial_call=True,
)
def apercu(sid, periode):
    if not sid:
        return html.Div("Sélectionnez un étudiant pour voir l'aperçu.",
                        style={"color":"var(--muted)","textAlign":"center","padding":"40px"})
    data = _get_donnees_etudiant(sid)
    if not data:
        return html.Div("Étudiant introuvable.")

    rows = []
    for cd in data["cours"]:
        col_note = "var(--red)" if cd["note"] < 10 else "var(--green)" if cd["note"] >= 14 else "var(--text-primary)"
        col_abs  = "var(--red)" if cd["taux_abs"] > 20 else "var(--text-primary)"
        rows.append(html.Tr([
            html.Td(cd["libelle"],    style={"fontWeight":"600"}),
            html.Td(cd["enseignant"],style={"color":"var(--muted)","fontSize":"12px"}),
            html.Td(f"{cd['note']:.2f}", style={"fontWeight":"700","color":col_note,"textAlign":"center"}),
            html.Td(str(int(cd["coef"])), style={"textAlign":"center","color":"var(--muted)"}),
            html.Td(cd["mention"],   style={"fontStyle":"italic","textAlign":"center"}),
            html.Td(f"{cd['nb_abs']}/{cd['nb_sess']}", style={"textAlign":"center","color":col_abs}),
        ]))

    moy = data["moy_gen"]
    col_moy = "var(--red)" if moy < 10 else "var(--green)" if moy >= 12 else "var(--copper)"
    mention_gen = ("Très Bien" if moy >= 16 else "Bien" if moy >= 14
                   else "Assez Bien" if moy >= 12 else "Passable" if moy >= 10
                   else "Insuffisant")

    return html.Div([
        # En-tête aperçu
        html.Div([
            html.Div("SGA PRO", style={"fontFamily":"Times New Roman,serif","fontSize":"24px",
                                        "fontWeight":"700","color":"var(--gold)","letterSpacing":"5px"}),
            html.Div(periode or "", style={"color":"var(--muted)","fontSize":"11px",
                                           "letterSpacing":"2px","marginTop":"4px"}),
        ], style={"textAlign":"center","padding":"20px 0","borderBottom":"2px solid var(--gold)",
                  "marginBottom":"16px"}),

        html.Div(f"{data['prenom']} {data['nom']}", style={
            "fontFamily":"Times New Roman,serif","fontSize":"20px","fontWeight":"700",
            "textAlign":"center","marginBottom":"4px",
        }),
        html.Div(data["email"], style={"textAlign":"center","color":"var(--muted)",
                                        "fontSize":"12px","marginBottom":"20px"}),

        # Tableau
        html.Table([
            html.Thead(html.Tr([
                html.Th(h) for h in ["Matière","Enseignant","Note","Coef.","Mention","Abs."]
            ])),
            html.Tbody(rows),
        ], className="sga-table", style={"width":"100%","marginBottom":"20px"}),

        # Moyenne
        html.Div([
            html.Div("Moyenne générale", style={"fontSize":"11px","letterSpacing":"2px",
                     "textTransform":"uppercase","color":"var(--muted)","marginBottom":"6px"}),
            html.Div(f"{moy:.2f} / 20", style={"fontFamily":"Times New Roman,serif",
                     "fontSize":"36px","fontWeight":"700","color":col_moy}),
            html.Div(mention_gen, style={"fontStyle":"italic","color":"var(--text-primary)",
                     "fontSize":"15px","marginTop":"4px"}),
        ], style={"textAlign":"center","padding":"20px","background":"var(--bg-secondary)",
                  "borderRadius":"4px","border":"1px solid var(--border)"}),
    ])


# ── TÉLÉCHARGEMENT PDF ────────────────────────────────────────────────────────
@callback(
    Output("dl-bulletin",    "data"),
    Output("bull-feedback",  "children"),
    Input("btn-gen-bull",    "n_clicks"),
    State("bull-stu",        "value"),
    State("bull-periode",    "value"),
    State("bull-appre",      "value"),
    prevent_initial_call=True,
)
def telecharger_bulletin(n, sid, periode, appre):
    if not sid:
        return None, html.Div("Sélectionnez un étudiant.",
                               className="sga-alert sga-alert-warning")
    data = _get_donnees_etudiant(sid)
    pdf  = _generer_pdf(data, periode or "Semestre 1", appre or "")
    if pdf is None:
        return None, html.Div(
            "⚠ reportlab non installé. Lancez : pip install reportlab",
            className="sga-alert sga-alert-danger")
    fname = f"bulletin_{data['nom']}_{data['prenom']}.pdf".replace(" ", "_")
    return dcc.send_bytes(pdf, filename=fname), html.Div(
        f"✓ {fname} généré.", className="sga-alert sga-alert-success")


@callback(
    Output("dl-all-bulletins",  "data"),
    Output("bull-all-feedback", "children"),
    Input("btn-gen-all",        "n_clicks"),
    State("bull-periode",       "value"),
    prevent_initial_call=True,
)
def telecharger_tous(n, periode):
    import zipfile
    db = SessionLocal()
    students = [(s.id, s.nom, s.prenom)
                for s in db.query(Student).filter_by(actif=True).order_by(Student.nom).all()]
    db.close()
    buf_zip = io.BytesIO()
    with zipfile.ZipFile(buf_zip, "w") as zf:
        for sid, nom, prenom in students:
            data = _get_donnees_etudiant(sid)
            pdf  = _generer_pdf(data, periode or "Semestre 1", "")
            if pdf:
                zf.writestr(f"bulletin_{nom}_{prenom}.pdf".replace(" ","_"), pdf)
    buf_zip.seek(0)
    return dcc.send_bytes(buf_zip.read(), filename="bulletins_promotion.zip"), html.Div(
        f"✓ {len(students)} bulletins générés.", className="sga-alert sga-alert-success")
