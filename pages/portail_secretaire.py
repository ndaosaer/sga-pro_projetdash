import dash
from dash import html, dcc, Input, Output, callback
from database import SessionLocal
from models import Student, Course, Session as Sess, Attendance
from datetime import date

dash.register_page(__name__, path="/portail-secretaire", name="Secrétariat")

def layout(**kwargs):
    return html.Div([
        dcc.Store(id="ps-trigger", data=1),
        html.Div([
            html.Div([
                html.Span("Nafa", style={"color":"var(--em)","fontFamily":"Instrument Serif,serif",
                    "fontSize":"20px","fontWeight":"400"}),
                html.Span(" Scolaire", style={"fontFamily":"Instrument Serif,serif",
                    "fontSize":"20px","fontStyle":"italic"}),
            ]),
            html.Div("Espace Secrétariat", style={"fontFamily":"Instrument Serif,serif",
                "fontSize":"22px","fontWeight":"400"}),
            dcc.Link("Déconnexion", href="/auth",
                     style={"fontSize":"10px","letterSpacing":"2px","color":"var(--muted)",
                            "textDecoration":"none","textTransform":"uppercase"}),
        ], className="topbar"),

        html.Div([
            html.Button("Étudiants",       id="ps-tab-stu", n_clicks=0, className="btn-sga btn-gold"),
            html.Button("Cours",           id="ps-tab-crs", n_clicks=0, className="btn-sga"),
            html.Button("Présences",       id="ps-tab-att", n_clicks=0, className="btn-sga"),
            html.Button("Calendrier",      id="ps-tab-cal", n_clicks=0, className="btn-sga"),
            html.Button(" Migration Excel", id="ps-tab-mig", n_clicks=0, className="btn-sga"),
        ], style={"display":"flex","gap":"8px","padding":"16px 24px","flexWrap":"wrap",
                  "borderBottom":"1px solid var(--border-lt)","background":"var(--bg-card)"}),

        html.Div(id="ps-content", style={"padding":"24px"}),
    ])


@callback(
    Output("ps-content","children"),
    Input("ps-tab-stu","n_clicks"),
    Input("ps-tab-crs","n_clicks"),
    Input("ps-tab-att","n_clicks"),
    Input("ps-tab-cal","n_clicks"),
    Input("ps-tab-mig","n_clicks"),
    Input("ps-trigger","data"),
)
def render_tab(n_stu, n_crs, n_att, n_cal, n_mig, trigger):
    ctx = dash.callback_context
    tab = "stu"
    if ctx.triggered:
        tid = ctx.triggered[0]["prop_id"].split(".")[0]
        if "crs" in tid: tab = "crs"
        elif "att" in tid: tab = "att"
        elif "cal" in tid: tab = "cal"
        elif "mig" in tid: tab = "mig"

    db = SessionLocal()
    try:
        if tab == "mig":
            from models import Classe
            from dash import dcc as _dcc
            import base64 as _b64, io as _io, pandas as _pd
            classe_opts = [{"label":f"{cl.code} - {cl.nom}","value":cl.id}
                           for cl in db.query(Classe).all()]
            db.close()
            return html.Div([
                html.Div([
                    html.Div("📥 Migration Excel → SQL", className="sga-card-title",
                             style={"marginBottom":"6px"}),
                    html.Div("Importez vos listes d'étudiants depuis Excel directement en base.",
                             style={"fontSize":"12px","color":"var(--text-muted)","marginBottom":"20px"}),
                    html.Div("Format attendu :", className="sga-label"),
                    html.Div([
                        html.Span(col, style={"padding":"4px 12px","background":"var(--em-pale)",
                            "color":"var(--em)","borderRadius":"20px","fontSize":"11px",
                            "fontWeight":"600","border":"1px solid rgba(14,102,85,0.2)"})
                        for col in ["Nom*","Prenom*","Email","Date_Naissance","Classe_Code","Telephone"]
                    ] + [html.Span("* obligatoires", style={"fontSize":"10px","color":"var(--muted)"})],
                    style={"display":"flex","flexWrap":"wrap","gap":"8px","marginBottom":"20px"}),
                    html.Div([
                        html.Div([html.Span("Classe par défaut", className="sga-label"),
                                  _dcc.Dropdown(id="ps-import-classe", options=classe_opts,
                                               placeholder="Si colonne Classe_Code absente...", clearable=True)],
                                 style={"flex":"1"}),
                        html.Div([html.Span("Mot de passe par défaut", className="sga-label"),
                                  _dcc.Input(id="ps-import-pwd", value="etu2026", className="sga-input",
                                            style={"width":"100%"})], style={"flex":"1"}),
                    ], style={"display":"flex","gap":"16px","marginBottom":"20px"}),
                    _dcc.Upload(id="ps-upload-etu",
                        children=html.Div([html.Div("",style={"fontSize":"32px","marginBottom":"8px"}),
                            html.Div("Glisser-déposer votre fichier Excel ici"),
                            html.A("parcourir",style={"color":"var(--em)","fontWeight":"700"}),
                            html.Div(".xlsx .xls .csv",style={"fontSize":"11px","color":"var(--muted)","marginTop":"6px"})],
                            style={"textAlign":"center"}),
                        className="upload-zone", style={"marginBottom":"16px","padding":"32px"}),
                    html.Div(id="ps-fb-import"),
                ], className="sga-card"),
            ])

        if tab == "stu":
            students = db.query(Student).order_by(Student.nom).all()
            rows = [html.Tr([
                html.Td(f"{s.nom} {s.prenom}", style={"fontWeight":"600"}),
                html.Td(s.email, style={"color":"var(--muted)","fontSize":"12px"}),
                html.Td(s.date_naissance.strftime("%d/%m/%Y") if s.date_naissance else "—",
                        style={"color":"var(--muted)","fontSize":"12px"}),
                html.Td(html.Span("Actif" if s.actif else "Inactif",
                        style={"color":"var(--green)" if s.actif else "var(--red)",
                               "fontWeight":"600","fontSize":"11px"})),
            ]) for s in students]
            return html.Div([
                html.Div([
                    html.Div(f"{len(students)} étudiants inscrits",
                             className="sga-card-title", style={"marginBottom":"16px"}),
                    html.Table([
                        html.Thead(html.Tr([
                            html.Th("Nom & Prénom"), html.Th("Email"),
                            html.Th("Date naissance"), html.Th("Statut"),
                        ])),
                        html.Tbody(rows),
                    ], className="sga-table", style={"width":"100%"}),
                ], className="sga-card"),
            ])

        elif tab == "crs":
            courses = db.query(Course).all()
            rows = [html.Tr([
                html.Td(c.code, style={"fontFamily":"JetBrains Mono,monospace","fontWeight":"600",
                                        "color":c.couleur or "var(--gold)"}),
                html.Td(c.libelle),
                html.Td(c.enseignant or "—", style={"color":"var(--muted)"}),
                html.Td(f"{c.volume_horaire}h", style={"fontFamily":"JetBrains Mono,monospace"}),
            ]) for c in courses]
            return html.Div([
                html.Div([
                    html.Div(f"{len(courses)} cours au programme",
                             className="sga-card-title", style={"marginBottom":"16px"}),
                    html.Table([
                        html.Thead(html.Tr([
                            html.Th("Code"), html.Th("Matière"),
                            html.Th("Enseignant"), html.Th("Volume"),
                        ])),
                        html.Tbody(rows),
                    ], className="sga-table", style={"width":"100%"}),
                ], className="sga-card"),
            ])

        elif tab == "att":
            sessions  = db.query(Sess).order_by(Sess.date.desc()).limit(30).all()
            atts      = db.query(Attendance).all()
            courses   = {c.code: c for c in db.query(Course).all()}
            att_count = {}
            for a in atts:
                att_count[a.id_session] = att_count.get(a.id_session, 0) + 1
            rows = [html.Tr([
                html.Td(s.date.strftime("%d/%m/%Y"),
                        style={"fontFamily":"JetBrains Mono,monospace"}),
                html.Td(s.course_code, style={"color":"var(--gold)","fontWeight":"600",
                         "fontFamily":"JetBrains Mono,monospace"}),
                html.Td(courses[s.course_code].libelle if s.course_code in courses else "—"),
                html.Td(f"{s.duree}h"),
                html.Td(str(att_count.get(s.id, 0)),
                        style={"color":"var(--red)" if att_count.get(s.id,0) > 0 else "var(--green)",
                               "fontWeight":"600"}),
            ]) for s in sessions]
            return html.Div([
                html.Div([
                    html.Div("30 dernières séances", className="sga-card-title",
                             style={"marginBottom":"16px"}),
                    html.Table([
                        html.Thead(html.Tr([
                            html.Th("Date"), html.Th("Code"),
                            html.Th("Matière"), html.Th("Durée"), html.Th("Absences"),
                        ])),
                        html.Tbody(rows),
                    ], className="sga-table", style={"width":"100%"}),
                ], className="sga-card"),
            ])

        else:  # cal
            today    = date.today()
            sessions = db.query(Sess).filter(Sess.date >= today).order_by(Sess.date).limit(20).all()
            courses  = {c.code: c for c in db.query(Course).all()}

            if sessions:
                items = []
                for s in sessions:
                    col = courses[s.course_code].couleur if s.course_code in courses else "var(--gold)"
                    lib = courses[s.course_code].libelle if s.course_code in courses else "—"
                    items.append(html.Div([
                        html.Div(style={"width":"4px","background":col,
                                        "borderRadius":"2px","flexShrink":"0"}),
                        html.Div([
                            html.Div(s.date.strftime("%A %d %B").capitalize(),
                                     style={"fontWeight":"700","fontSize":"14px"}),
                            html.Div(f"{s.course_code} — {lib}",
                                     style={"color":"var(--muted)","fontSize":"12px"}),
                            html.Div(s.theme or "—",
                                     style={"color":"var(--gold)","fontSize":"12px"}),
                        ]),
                        html.Div(f"{s.duree}h",
                                 style={"fontFamily":"JetBrains Mono,monospace",
                                        "color":"var(--gold)","fontWeight":"700",
                                        "marginLeft":"auto"}),
                    ], style={"display":"flex","gap":"12px","alignItems":"center",
                              "padding":"14px","background":"var(--bg-secondary)",
                              "borderRadius":"4px","marginBottom":"8px"}))
            else:
                items = [html.Div("Aucune séance planifiée.",
                                  style={"color":"var(--muted)","textAlign":"center","padding":"40px"})]

            return html.Div([
                html.Div([
                    html.Div("Prochaines séances planifiées", className="sga-card-title",
                             style={"marginBottom":"16px"}),
                    *items,
                ], className="sga-card"),
            ])

    finally:
        db.close()


# ── Callback import Excel étudiants (portail secrétaire) ──────────────────────
from dash import callback as _cb, Input as _In, Output as _Out, State as _St
import pandas as pd, base64, io

@_cb(
    _Out("ps-fb-import", "children"),
    _In("ps-upload-etu", "contents"),
    _St("ps-upload-etu", "filename"),
    _St("ps-import-classe", "value"),
    _St("ps-import-pwd",    "value"),
    prevent_initial_call=True,
)
def ps_import_etu(contents, fname, default_classe_id, default_pwd):
    if not contents:
        return dash.no_update
    from werkzeug.security import generate_password_hash
    from models import User, Classe
    from datetime import datetime
    try:
        _, cs = contents.split(",")
        raw = base64.b64decode(cs)
        df = pd.read_csv(io.StringIO(raw.decode("utf-8","replace"))) if (fname or "").lower().endswith(".csv") else pd.read_excel(io.BytesIO(raw))
        df.columns = [c.strip().lower().replace(" ","_") for c in df.columns]

        def fc(keys):
            for k in keys:
                if k in df.columns: return k
            return None

        c_nom    = fc(["nom","last_name","name"])
        c_prenom = fc(["prenom","prénom","first_name","firstname"])
        c_email  = fc(["email","mail","courriel"])
        c_dob    = fc(["date_naissance","dob","birth_date","naissance"])
        c_classe = fc(["classe_code","classe","class","niveau"])

        if not c_nom or not c_prenom:
            return html.Div(f" Colonnes Nom/Prénom introuvables. Colonnes : {', '.join(df.columns.tolist())}",
                            className="sga-alert sga-alert-danger")

        db = SessionLocal()
        classes_by_code = {cl.code.upper(): cl.id for cl in db.query(Classe).all()}
        pwd_hash = generate_password_hash(default_pwd or "etu2026")
        imported = skipped = 0; errors = []

        for idx, row in df.iterrows():
            try:
                nom    = str(row[c_nom]).strip().upper()
                prenom = str(row[c_prenom]).strip().title()
                if not nom or nom == "NAN": continue
                if db.query(Student).filter(Student.nom==nom, Student.prenom==prenom).first():
                    skipped += 1; continue
                email = str(row[c_email]).strip() if c_email and not pd.isna(row.get(c_email,"")) else f"{prenom.lower()}.{nom.lower()}@ecole.sn"
                classe_id = default_classe_id
                if c_classe and not pd.isna(row.get(c_classe,"")):
                    code = str(row[c_classe]).strip().upper()
                    if code in classes_by_code: classe_id = classes_by_code[code]
                dob = None
                if c_dob and not pd.isna(row.get(c_dob,"")):
                    try: dob = pd.to_datetime(row[c_dob]).date()
                    except: pass
                stu = Student(); stu.nom=nom; stu.prenom=prenom; stu.email=email
                stu.date_naissance=dob; stu.classe_id=classe_id; stu.actif=True
                stu.created_at=datetime.now()
                db.add(stu); db.flush()
                uname = f"{prenom.lower().replace(' ','').replace('é','e').replace('è','e')}.{nom.lower().replace(' ','')}"
                base_u = uname; sfx = 1
                while db.query(User).filter_by(username=uname).first():
                    uname = f"{base_u}{sfx}"; sfx += 1
                u = User(); u.username=uname; u.password_hash=pwd_hash
                u.role="student"; u.linked_id=stu.id; u.created_at=datetime.now()
                db.add(u); imported += 1
            except Exception as e:
                errors.append(f"Ligne {idx+2}: {e}")

        db.commit(); db.close()
        items = [html.Div(f" {imported} étudiant(s) importé(s).", className="sga-alert sga-alert-success")]
        if skipped: items.append(html.Div(f" {skipped} doublon(s) ignoré(s).", className="sga-alert sga-alert-warning"))
        if errors:  items.append(html.Div(f" {len(errors)} erreur(s).", className="sga-alert sga-alert-danger"))
        return html.Div(items)
    except Exception as e:
        return html.Div(f" Erreur fichier : {e}", className="sga-alert sga-alert-danger")
