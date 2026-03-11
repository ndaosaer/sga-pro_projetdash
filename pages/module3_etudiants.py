import dash
from dash import html, dcc, Input, Output, State, callback, ALL
import plotly.graph_objects as go
import pandas as pd, base64, io
from database import SessionLocal
from models import Classe, Student, Grade, Course, Attendance, Session

dash.register_page(__name__, path="/etudiants", name="Etudiants")

def layout():
    db = SessionLocal()
    c_opts = [{"label":f"{c.code} - {c.libelle}","value":c.code} for c in db.query(Course).all()]
    classe_opts_e = [{"label":f"{cl.code} - {cl.nom}","value":cl.id} for cl in db.query(Classe).all()]
    db.close()
    return html.Div([
        dcc.Store(id='etu-classe-opts', data=classe_opts_e),
        dcc.Store(id='etu-tab-store', data='liste'),
        html.Div([
            html.Div([html.Div("Gestion des Étudiants", className="page-title"),
                      html.Div("Fiches individuelles · Notes · Migration Excel → SQL", className="page-subtitle")]),
        ], className="topbar"),

        html.Div([
            html.Button("👨\u200d🎓  Promotion",       id="etu-tab-liste",  n_clicks=0, className="btn-sga btn-gold", style={"fontWeight":"700"}),
            html.Button("📥  Migration Excel", id="etu-tab-import", n_clicks=0, className="btn-sga"),
            html.Button("📊  Notes & Export",  id="etu-tab-notes",  n_clicks=0, className="btn-sga"),
        ], style={"display":"flex","gap":"8px","marginBottom":"20px"}),

        html.Div([
            html.Div([
                html.Div("Promotion", className="sga-card-title", style={"marginBottom":"16px"}),
                html.Div(id="student-list"),
                dcc.Interval(id="iv-stu", interval=3000, max_intervals=1),
            ], className="sga-card", style={"width":"260px","minWidth":"0","flexShrink":"0","overflowY":"auto","overflowX":"hidden","maxHeight":"78vh"}),
            html.Div(id="fiche-detail", style={"flex":"1"}),
        ], id="etu-panel-liste", style={"display":"flex","gap":"20px","marginBottom":"24px"}),

        html.Div([
            html.Div([
                html.Div("📥 Migration Excel → SQL", className="sga-card-title", style={"marginBottom":"6px"}),
                html.Div("Importez vos listes depuis Excel directement en base de données.", style={"fontSize":"12px","color":"var(--text-muted)","marginBottom":"20px"}),
                html.Div("Format attendu :", className="sga-label"),
                html.Div([
                    *[html.Span(col, style={"padding":"4px 12px","background":"var(--em-pale)","color":"var(--em)","borderRadius":"20px","fontSize":"11px","fontWeight":"600","border":"1px solid rgba(14,102,85,0.2)"})
                      for col in ["Nom*","Prenom*","Email","Date_Naissance","Classe_Code","Telephone"]],
                    html.Span("* obligatoires", style={"fontSize":"10px","color":"var(--muted)"}),
                ], style={"display":"flex","flexWrap":"wrap","gap":"8px","marginBottom":"20px"}),
                html.Div([
                    html.Div([html.Span("Classe par défaut", className="sga-label"),
                              dcc.Dropdown(id="dd-import-classe", options=classe_opts_e, placeholder="Si colonne Classe_Code absente...", clearable=True)], style={"flex":"1"}),
                    html.Div([html.Span("Mot de passe par défaut", className="sga-label"),
                              dcc.Input(id="inp-import-pwd", value="etu2026", className="sga-input", placeholder="etu2026", style={"width":"100%"})], style={"flex":"1"}),
                ], style={"display":"flex","gap":"16px","marginBottom":"20px"}),
                dcc.Upload(id="upload-etudiants",
                    children=html.Div([html.Div("📁", style={"fontSize":"32px","marginBottom":"8px"}),
                        html.Div("Glisser-déposer votre fichier Excel ici"),
                        html.A("parcourir", style={"color":"var(--em)","fontWeight":"700"}),
                        html.Div(".xlsx, .xls, .csv acceptés", style={"fontSize":"11px","color":"var(--muted)","marginTop":"6px"})], style={"textAlign":"center"}),
                    className="upload-zone", style={"marginBottom":"16px","padding":"32px"}),
                html.Div(id="fb-import-etu"),
            ], className="sga-card"),
        ], id="etu-panel-import", style={"display":"none"}),

        html.Div([
        html.Div([
            html.Div([
                html.Div("Import / Export des Notes", className="sga-card-title", style={"marginBottom":"20px"}),
                html.Div([
                    html.Div([html.Span("Cours cible", className="sga-label"),
                              dcc.Dropdown(id="dd-cnotes", options=c_opts, placeholder="Cours...")
                          ]),
                          html.Div([html.Label("Classe", style={"fontSize":"12px","color":"var(--muted)","marginBottom":"4px"}),
                          dcc.Dropdown(id="dd-classe-etu", placeholder="Toutes les classes", clearable=True)]),
                    html.Div([html.Span(" ", className="sga-label"),
                              html.Div([
                                  html.Button("Template Excel", id="btn-tmpl", className="btn-sga btn-cyan"),
                                  dcc.Download(id="dl-tmpl"),
                              ]),
                              ]),
                ], style={"display":"flex","gap":"16px","alignItems":"flex-end","marginBottom":"8px"}),
                html.Div(id="fb-tmpl", style={"marginBottom":"12px","fontSize":"12px"}),
                dcc.Upload(id="upload-notes",
                    children=html.Div(["Glisser-deposer le fichier Excel, ou ", html.A("parcourir")]),
                    className="upload-zone"),
                html.Div(id="fb-upload", style={"marginTop":"12px"}),
            ], className="sga-card"),
        ]),
    ])
        ], id="etu-panel-notes", style={"display":"none"}),



@callback(Output("dd-classe-etu","options"), Input("etu-classe-opts","data"))
def load_classe_opts_etu(data): return data or []


@callback(Output("student-list","children"), Input("iv-stu","n_intervals"))
def load_list(_):
    db = SessionLocal()
    classes  = db.query(Classe).filter_by(actif=True).order_by(Classe.nom).all()
    classe_opts_e = [{"label": c.nom, "value": c.id} for c in classes]
    students = db.query(Student).filter_by(actif=True).order_by(Student.nom).all()
    grades   = db.query(Grade).all()
    # Calculer moyennes dans la session
    stu_data = []
    for s in students:
        g = [gr for gr in grades if gr.id_student == s.id]
        tc = sum(gr.coefficient for gr in g)
        moy = round(sum(gr.note*gr.coefficient for gr in g)/tc,2) if tc else None
        stu_data.append((s.id, s.nom, s.prenom, moy))
    db.close()
    return html.Div([
        html.Div([
            html.Div(f"{nom[0]}{prenom[0]}", style={
                "width":"32px","height":"32px","borderRadius":"8px","flexShrink":"0",
                "background":"linear-gradient(135deg,var(--cyan),var(--green))",
                "display":"flex","alignItems":"center","justifyContent":"center",
                "fontSize":"11px","fontWeight":"700","color":"var(--bg-primary)",
            }),
            html.Div([
                html.Div(f"{nom} {prenom}", style={
                    "fontSize":"12px","fontWeight":"600",
                    "overflow":"hidden","textOverflow":"ellipsis","whiteSpace":"nowrap"
                }),
                html.Div(f"Moy: {moy}/20" if moy else "---",
                         style={"fontSize":"10px","color":"var(--text-muted)"}),
            ], style={"minWidth":"0","flex":"1"}),
        ], id={"type":"stu-item","index":sid},
           style={"display":"flex","gap":"10px","alignItems":"center",
                  "padding":"10px 8px","borderRadius":"8px","cursor":"pointer",
                  "transition":"background 0.15s","borderBottom":"1px solid rgba(255,255,255,0.04)",
                  "overflow":"hidden","width":"100%","boxSizing":"border-box"})
        for sid, nom, prenom, moy in stu_data
    ])

@callback(Output("fiche-detail","children"),
          Input({"type":"stu-item","index":ALL},"n_clicks"),
          State({"type":"stu-item","index":ALL},"id"),
          prevent_initial_call=True)
def show_fiche(clicks, ids):
    from dash import ctx
    if not ctx.triggered_id: return ""
    return build_fiche(ctx.triggered_id["index"])

def build_fiche(sid):
    db = SessionLocal()
    s = db.get(Student, sid)
    if not s: db.close(); return html.Div("Etudiant introuvable.")
    grades   = db.query(Grade).filter_by(id_student=sid).all()
    absences = db.query(Attendance).filter_by(id_student=sid).count()
    total_s  = db.query(Session).count()
    courses  = {c.code: c.libelle for c in db.query(Course).all()}

    # Calculer tout dans la session
    tc  = sum(g.coefficient for g in grades)
    moy = round(sum(g.note*g.coefficient for g in grades)/tc,2) if tc else None
    taux = round(absences/total_s*100,1) if total_s else 0
    nom, prenom, email = s.nom, s.prenom, s.email
    dob = s.date_naissance
    grade_data = [(g.course_code, g.note, g.coefficient) for g in grades]
    db.close()

    cat  = [courses.get(code, code)[:12] for code, note, coef in grade_data]
    vals = [note for code, note, coef in grade_data]

    fig = go.Figure()
    if len(cat) >= 3:
        fig.add_trace(go.Scatterpolar(
            r=vals+[vals[0]], theta=cat+[cat[0]],
            fill="toself", fillcolor="rgba(0,212,255,0.1)",
            line=dict(color="#00d4ff",width=2), marker=dict(size=6,color="#00d4ff"),
        ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="JetBrains Mono",color="#64748b",size=10),
        margin=dict(l=40,r=40,t=40,b=40),
        polar=dict(bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True,range=[0,20],gridcolor="rgba(0,212,255,0.1)",
                            tickfont=dict(color="#64748b",size=9)),
            angularaxis=dict(gridcolor="rgba(0,212,255,0.1)",tickfont=dict(color="#e2e8f0",size=10))),
        showlegend=False,
    )

    return html.Div([
        html.Div([
            html.Div([
                html.Div(f"{nom[0]}{prenom[0]}", style={
                    "width":"56px","height":"56px","borderRadius":"12px",
                    "background":"linear-gradient(135deg,var(--cyan),var(--green))",
                    "display":"flex","alignItems":"center","justifyContent":"center",
                    "fontSize":"20px","fontWeight":"700","color":"var(--bg-primary)",
                }),
                html.Div([
                    html.Div(f"{prenom} {nom}", style={"fontSize":"22px","fontFamily":"Rajdhani","fontWeight":"700"}),
                    html.Div(email, style={"color":"var(--text-muted)","fontSize":"12px"}),
                    html.Div(dob.strftime("%d/%m/%Y") if dob else "---",
                             style={"color":"var(--text-muted)","fontSize":"11px"}),
                ]),
            ], style={"display":"flex","gap":"16px","alignItems":"center"}),
        ], className="sga-card", style={"marginBottom":"16px"}),

        html.Div([
            html.Div([html.Div(f"{moy}/20" if moy else "---",className="kpi-value"),html.Div("Moyenne generale",className="kpi-label")],className="kpi-card kpi-cyan"),
            html.Div([html.Div(str(absences),className="kpi-value"),html.Div("Absences totales",className="kpi-label")],className=f"kpi-card {'kpi-red' if taux>20 else 'kpi-orange' if taux>10 else 'kpi-green'}"),
            html.Div([html.Div(f"{taux}%",className="kpi-value"),html.Div("Taux absenteisme",className="kpi-label")],className="kpi-card kpi-orange"),
            html.Div([html.Div(str(len(grade_data)),className="kpi-value"),html.Div("Cours evalues",className="kpi-label")],className="kpi-card kpi-purple"),
        ], style={"display":"grid","gridTemplateColumns":"repeat(4,1fr)","gap":"12px","marginBottom":"16px"}),

        html.Div([
            html.Div([
                html.Div("Profil academique", className="sga-card-title", style={"marginBottom":"12px"}),
                dcc.Graph(figure=fig, config={"displayModeBar":False}, style={"height":"250px"}),
            ], className="sga-card", style={"flex":"1"}),
            html.Div([
                html.Div("Detail des notes", className="sga-card-title", style={"marginBottom":"12px"}),
                html.Table([
                    html.Thead(html.Tr([html.Th(h) for h in ["Cours","Note","Coef.","Mention"]])),
                    html.Tbody([html.Tr([
                        html.Td(code, style={"color":"var(--cyan)","fontWeight":"600"}),
                        html.Td(f"{note:.2f}/20"),
                        html.Td(f"x{coef}"),
                        html.Td(html.Span(
                            "TB" if note>=16 else "B" if note>=14 else "AB" if note>=12 else "P" if note>=10 else "F",
                            className=f"tag {'tag-green' if note>=16 else 'tag-cyan' if note>=12 else 'tag-orange' if note>=10 else 'tag-red'}",
                        )),
                    ]) for code, note, coef in grade_data]),
                ], className="sga-table", style={"width":"100%"}),
            ], className="sga-card", style={"flex":"1"}),
        ], style={"display":"flex","gap":"16px"}),
    ])

@callback(Output("dl-tmpl","data"), Output("fb-tmpl","children"),
          Input("btn-tmpl","n_clicks"), State("dd-cnotes","value"), prevent_initial_call=True)
def dl_template(n, code):
    if not code:
        return None, html.Div("⚠ Sélectionnez d'abord un cours dans le menu déroulant.",
                              style={"color":"var(--gold)","fontSize":"12px","marginTop":"6px"})
    db = SessionLocal()
    students = [(s.id, s.nom, s.prenom) for s in db.query(Student).filter_by(actif=True).order_by(Student.nom).all()]
    db.close()
    rows = [{"ID":sid,"Nom":nom,"Prenom":prenom,"Note":"","Coefficient":1.0} for sid,nom,prenom in students]
    df = pd.DataFrame(rows)
    try:
        import openpyxl  # noqa
        buf = io.BytesIO()
        df.to_excel(buf, index=False, engine="openpyxl")
        buf.seek(0)
        return dcc.send_bytes(buf.read(), filename=f"notes_{code}.xlsx"),                html.Div("✓ Template téléchargé.", style={"color":"var(--green)","fontSize":"12px"})
    except ModuleNotFoundError:
        # Fallback CSV si openpyxl absent
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        buf.seek(0)
        return dcc.send_string(buf.read(), filename=f"notes_{code}.csv"),                html.Div("⚠ openpyxl manquant — fichier CSV téléchargé à la place.",
                        style={"color":"var(--gold)","fontSize":"12px"})

@callback(Output("fb-upload","children"),
          Input("upload-notes","contents"), State("upload-notes","filename"), State("dd-cnotes","value"),
          prevent_initial_call=True)
def upload(contents, fname, code):
    if not contents or not code:
        return html.Div("Selectionnez un cours avant d importer.", className="sga-alert sga-alert-warning")
    try:
        _, cs = contents.split(",")
        df = pd.read_excel(io.BytesIO(base64.b64decode(cs)))
        if not {"ID","Note","Coefficient"}.issubset(df.columns):
            return html.Div("Colonnes manquantes: ID, Note, Coefficient.", className="sga-alert sga-alert-danger")
        db = SessionLocal(); updated = 0
        for _,row in df.iterrows():
            if pd.isna(row["Note"]): continue
            ex = db.query(Grade).filter_by(id_student=int(row["ID"]),course_code=code).first()
            if ex: ex.note=float(row["Note"]); ex.coefficient=float(row["Coefficient"])
            else: db.add(Grade(id_student=int(row["ID"]),course_code=code,note=float(row["Note"]),coefficient=float(row["Coefficient"])))
            updated+=1
        db.commit(); db.close()
        return html.Div(f"{updated} note(s) importee(s).", className="sga-alert sga-alert-success")
    except Exception as e:
        return html.Div(str(e), className="sga-alert sga-alert-danger")


# ── Switcher onglets étudiants ─────────────────────────────────────────────────
@callback(
    Output("etu-panel-liste",  "style"),
    Output("etu-panel-import", "style"),
    Output("etu-panel-notes",  "style"),
    Output("etu-tab-liste",    "className"),
    Output("etu-tab-import",   "className"),
    Output("etu-tab-notes",    "className"),
    Output("etu-tab-store",    "data"),
    Input("etu-tab-liste",  "n_clicks"),
    Input("etu-tab-import", "n_clicks"),
    Input("etu-tab-notes",  "n_clicks"),
    State("etu-tab-store",  "data"),
)
def switch_etu_tab(n_l, n_i, n_n, current):
    from dash import ctx as _ctx
    show_flex = {"display":"flex","gap":"20px","marginBottom":"24px"}
    show_blk  = {"display":"block","marginBottom":"24px"}
    hide      = {"display":"none"}
    active    = "btn-sga btn-gold"
    normal    = "btn-sga"
    tid = _ctx.triggered_id or "etu-tab-liste"
    if tid == "etu-tab-import":
        return hide, show_blk, hide, normal, active, normal, "import"
    if tid == "etu-tab-notes":
        return hide, hide, show_blk, normal, normal, active, "notes"
    return show_flex, hide, hide, active, normal, normal, "liste"


# ── Import Excel → SQL étudiants ──────────────────────────────────────────────
@callback(
    Output("fb-import-etu", "children"),
    Input("upload-etudiants", "contents"),
    State("upload-etudiants", "filename"),
    State("dd-import-classe",  "value"),
    State("inp-import-pwd",    "value"),
    prevent_initial_call=True,
)
def import_etudiants_excel(contents, fname, default_classe_id, default_pwd):
    if not contents:
        return dash.no_update

    from werkzeug.security import generate_password_hash
    from models import User
    from datetime import datetime, date

    try:
        _, cs = contents.split(",")
        raw = base64.b64decode(cs)

        # Lire selon format
        if fname and fname.lower().endswith(".csv"):
            df = pd.read_csv(io.StringIO(raw.decode("utf-8", errors="replace")))
        else:
            df = pd.read_excel(io.BytesIO(raw))

        # Normaliser les colonnes (insensible à la casse)
        df.columns = [c.strip().lower().replace(" ","_") for c in df.columns]
        col_map = {
            "nom":       ["nom","last_name","lastname","name"],
            "prenom":    ["prenom","prénom","first_name","firstname","prenom"],
            "email":     ["email","mail","courriel","e-mail"],
            "dob":       ["date_naissance","dob","date_de_naissance","birth_date","naissance"],
            "classe":    ["classe_code","classe","class","niveau","class_code"],
            "telephone": ["telephone","téléphone","tel","phone","mobile"],
        }
        def find_col(df, keys):
            for k in keys:
                if k in df.columns: return k
            return None

        c_nom    = find_col(df, col_map["nom"])
        c_prenom = find_col(df, col_map["prenom"])
        c_email  = find_col(df, col_map["email"])
        c_dob    = find_col(df, col_map["dob"])
        c_classe = find_col(df, col_map["classe"])
        c_tel    = find_col(df, col_map["telephone"])

        if not c_nom or not c_prenom:
            return html.Div(
                f"❌ Colonnes 'Nom' et 'Prénom' introuvables. Colonnes détectées : {', '.join(df.columns.tolist())}",
                className="sga-alert sga-alert-danger")

        db = SessionLocal()

        # Construire index des classes
        from models import Classe
        classes_by_code = {cl.code.upper(): cl.id for cl in db.query(Classe).all()}
        classes_by_id   = {cl.id: cl.id for cl in db.query(Classe).all()}

        pwd_hash = generate_password_hash(default_pwd or "etu2026")
        imported = 0; skipped = 0; errors = []

        for idx, row in df.iterrows():
            try:
                nom    = str(row[c_nom]).strip().upper()
                prenom = str(row[c_prenom]).strip().title()
                if not nom or not prenom or nom == "NAN": continue

                email = str(row[c_email]).strip() if c_email and not pd.isna(row.get(c_email,"")) else f"{prenom.lower().replace(' ','.')}.{nom.lower().replace(' ','.')}@ecole.sn"

                # Classe
                classe_id = default_classe_id
                if c_classe and not pd.isna(row.get(c_classe,"")):
                    code = str(row[c_classe]).strip().upper()
                    if code in classes_by_code:
                        classe_id = classes_by_code[code]

                # Date naissance
                dob = None
                if c_dob and not pd.isna(row.get(c_dob,"")):
                    try:
                        dob = pd.to_datetime(row[c_dob]).date()
                    except Exception:
                        pass

                # Vérifier doublon
                existing = db.query(Student).filter(
                    Student.nom == nom, Student.prenom == prenom
                ).first()
                if existing:
                    skipped += 1
                    continue

                # Créer étudiant
                stu = Student()
                stu.nom            = nom
                stu.prenom         = prenom
                stu.email          = email
                stu.date_naissance = dob
                stu.classe_id      = classe_id
                stu.actif          = True
                stu.created_at     = datetime.now()
                db.add(stu)
                db.flush()

                # Créer compte utilisateur
                uname = f"{prenom.lower().replace(' ','').replace('é','e').replace('è','e').replace('ê','e')}.{nom.lower().replace(' ','')}"
                # Éviter doublons username
                suffix = 1
                base_uname = uname
                while db.query(User).filter_by(username=uname).first():
                    uname = f"{base_uname}{suffix}"
                    suffix += 1

                u = User()
                u.username      = uname
                u.password_hash = pwd_hash
                u.role          = "student"
                u.linked_id     = stu.id
                u.created_at    = datetime.now()
                db.add(u)

                imported += 1

            except Exception as e:
                errors.append(f"Ligne {idx+2} : {str(e)}")

        db.commit()
        db.close()

        items = [
            html.Div(f"✅ {imported} étudiant(s) importé(s) avec succès.",
                     className="sga-alert sga-alert-success"),
        ]
        if skipped:
            items.append(html.Div(f"⚠ {skipped} doublon(s) ignoré(s) (nom+prénom déjà existant).",
                                  className="sga-alert sga-alert-warning"))
        if errors:
            items.append(html.Div([
                html.Div(f"❌ {len(errors)} erreur(s) :", className="sga-alert sga-alert-danger"),
                html.Ul([html.Li(e, style={"fontSize":"11px"}) for e in errors[:10]]),
            ]))

        return html.Div(items)

    except Exception as e:
        return html.Div(f"❌ Erreur de lecture du fichier : {str(e)}",
                        className="sga-alert sga-alert-danger")
