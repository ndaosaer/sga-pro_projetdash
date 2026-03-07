import dash, base64, os, uuid
from dash import html, dcc, Input, Output, State, callback, ctx
from database import SessionLocal
from models import User, Conversation, ConvParticipant, Message
from datetime import datetime

dash.register_page(__name__, path="/messagerie", name="Messagerie")

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ROLE_LABELS = {
    "admin":     "Directeur",
    "teacher":   "Enseignant",
    "secretary": "Secretaire",
    "student":   "Etudiant",
    "parent":    "Parent",
}
ROLE_COLORS = {
    "admin":     "var(--gold)",
    "teacher":   "var(--green)",
    "secretary": "var(--copper)",
    "student":   "var(--muted)",
    "parent":    "var(--muted)",
}


def layout():
    return html.Div([
        dcc.Store(id="msg-refresh",  data=0),
        dcc.Store(id="msg-conv-id",  data=None),
        dcc.Interval(id="msg-poll",  interval=30_000, n_intervals=0),

        html.Div([
            html.Div([
                html.Div("Messagerie", className="page-title"),
                html.Div("Communications internes", className="page-subtitle"),
            ]),
            html.Button("+ Nouvelle conversation", id="btn-msg-new",
                        n_clicks=0, className="btn-sga btn-gold"),
        ], className="topbar"),

        html.Div([
            # Colonne gauche — liste des conversations
            html.Div([
                html.Div(id="msg-conv-list",
                         style={"overflowY":"auto","maxHeight":"calc(100vh - 180px)"}),
            ], style={"width":"320px","flexShrink":"0","background":"var(--bg-card)",
                      "border":"1px solid var(--border)","borderRadius":"6px","overflow":"hidden"}),

            # Colonne droite — fil de conversation
            html.Div(id="msg-thread",
                     style={"flex":"1","background":"var(--bg-card)",
                            "border":"1px solid var(--border)","borderRadius":"6px",
                            "display":"flex","flexDirection":"column"}),
        ], style={"display":"flex","gap":"16px","padding":"24px",
                  "height":"calc(100vh - 120px)"}),

        # ── Modal nouvelle conversation ──
        html.Div([
            html.Div([
                html.Div("Nouvelle conversation", className="sga-card-title",
                         style={"marginBottom":"20px"}),

                html.Div("Type", className="sga-label"),
                dcc.RadioItems(id="msg-nc-type",
                               options=[{"label":"Message prive","value":"prive"},
                                        {"label":"Message de groupe","value":"groupe"}],
                               value="prive", inline=True,
                               style={"marginBottom":"16px","fontSize":"13px","gap":"16px"}),

                html.Div("Destinataire(s)", className="sga-label"),
                dcc.Dropdown(id="msg-nc-dest", placeholder="Selectionner...",
                             multi=True, style={"marginBottom":"14px"}),

                html.Div("Sujet", className="sga-label"),
                dcc.Input(id="msg-nc-sujet", placeholder="Sujet de la conversation",
                          className="sga-input",
                          style={"width":"100%","marginBottom":"14px"}),

                html.Div("Premier message", className="sga-label"),
                dcc.Textarea(id="msg-nc-message", placeholder="Ecrivez votre message...",
                             style={"width":"100%","minHeight":"100px","marginBottom":"14px",
                                    "background":"var(--bg-primary)","border":"1px solid var(--border)",
                                    "borderRadius":"4px","padding":"10px",
                                    "color":"var(--text-primary)",
                                    "fontFamily":"JetBrains Mono,monospace","fontSize":"13px",
                                    "resize":"vertical"}),

                html.Div("Piece jointe (optionnel)", className="sga-label"),
                dcc.Upload(id="msg-nc-upload",
                           children=html.Div([
                               html.Span("Deposer un fichier ou "),
                               html.Span("parcourir", style={"color":"var(--gold)",
                                         "textDecoration":"underline","cursor":"pointer"}),
                           ], style={"fontSize":"12px","color":"var(--muted)"}),
                           style={"border":"1px dashed var(--border)","borderRadius":"4px",
                                  "padding":"16px","textAlign":"center","marginBottom":"20px",
                                  "cursor":"pointer","background":"var(--bg-secondary)"},
                           max_size=5_000_000),

                html.Div([
                    html.Button("Envoyer", id="btn-msg-nc-send", n_clicks=0,
                                className="btn-sga btn-gold"),
                    html.Button("Annuler", id="btn-msg-nc-cancel", n_clicks=0,
                                className="btn-sga"),
                ], style={"display":"flex","gap":"10px"}),
                html.Div(id="msg-nc-feedback", style={"marginTop":"12px"}),
            ], style={"background":"var(--bg-card)","border":"1px solid var(--border)",
                      "borderRadius":"6px","padding":"32px","width":"540px","margin":"0 auto"}),
        ], id="modal-nc-msg",
           style={"display":"none","position":"fixed","inset":"0",
                  "background":"rgba(0,0,0,0.5)","zIndex":"999",
                  "alignItems":"center","justifyContent":"center"}),
    ])


# ── Charger destinataires ──
@callback(
    Output("msg-nc-dest","options"),
    Input("msg-refresh","data"),
    State("session-store","data"),
)
def load_users(refresh, session):
    if not session:
        return []
    db = SessionLocal()
    try:
        me = session.get("user_id")
        users = db.query(User).filter(User.id != me).order_by(User.role, User.username).all()
        return [{"label": f"{u.username} — {ROLE_LABELS.get(u.role, u.role)}",
                 "value": u.id} for u in users]
    finally:
        db.close()


# ── Toggle modal ──
@callback(
    Output("modal-nc-msg","style"),
    Input("btn-msg-new","n_clicks"),
    Input("btn-msg-nc-cancel","n_clicks"),
    Input("btn-msg-nc-send","n_clicks"),
    prevent_initial_call=True,
)
def toggle_modal(n1, n2, n3):
    show = {"display":"flex","position":"fixed","inset":"0",
            "background":"rgba(0,0,0,0.5)","zIndex":"999",
            "alignItems":"center","justifyContent":"center"}
    if ctx.triggered_id == "btn-msg-new":
        return show
    return {"display":"none"}


# ── Creer conversation ──
@callback(
    Output("msg-nc-feedback","children"),
    Output("msg-refresh","data", allow_duplicate=True),
    Output("msg-conv-id","data", allow_duplicate=True),
    Input("btn-msg-nc-send","n_clicks"),
    State("msg-nc-dest","value"),
    State("msg-nc-sujet","value"),
    State("msg-nc-message","value"),
    State("msg-nc-type","value"),
    State("msg-nc-upload","contents"),
    State("msg-nc-upload","filename"),
    State("session-store","data"),
    State("msg-refresh","data"),
    prevent_initial_call=True,
)
def creer_conv(n, dest_ids, sujet, message, type_conv, upload_content, upload_name, session, refresh):
    if not session:
        return html.Div("Non connecte.", className="sga-alert sga-alert-danger"), dash.no_update, dash.no_update
    if not dest_ids or not sujet or not message:
        return html.Div("Destinataire, sujet et message sont requis.",
                        className="sga-alert sga-alert-warning"), dash.no_update, dash.no_update

    sender_id = session.get("user_id")
    db = SessionLocal()
    try:
        # Piece jointe
        pj_path = pj_nom = pj_type = None
        if upload_content and upload_name:
            ext  = upload_name.rsplit(".", 1)[-1].lower() if "." in upload_name else ""
            pj_type = "pdf" if ext == "pdf" else "image" if ext in ("png","jpg","jpeg","gif","webp") else "fichier"
            fname   = f"{uuid.uuid4().hex[:12]}_{upload_name}"
            fpath   = os.path.join(UPLOAD_DIR, fname)
            content_str = upload_content.split(",")[1] if "," in upload_content else upload_content
            with open(fpath, "wb") as f:
                f.write(base64.b64decode(content_str))
            pj_path = f"/assets/uploads/{fname}"
            pj_nom  = upload_name

        # Creer la conversation
        conv = Conversation()
        conv.sujet      = sujet
        conv.type_conv  = type_conv
        conv.created_by = sender_id
        conv.created_at = datetime.now()
        db.add(conv)
        db.flush()

        # Participants : expediteur + destinataires
        all_ids = list(set([sender_id] + (dest_ids if isinstance(dest_ids, list) else [dest_ids])))
        for uid in all_ids:
            p = ConvParticipant()
            p.conversation_id = conv.id
            p.user_id         = uid
            p.lu_at           = datetime.now() if uid == sender_id else None
            db.add(p)

        # Premier message
        msg = Message()
        msg.conversation_id = conv.id
        msg.sender_id       = sender_id
        msg.contenu         = message
        msg.piece_jointe    = pj_path
        msg.pj_nom          = pj_nom
        msg.pj_type         = pj_type
        msg.created_at      = datetime.now()
        db.add(msg)
        db.commit()

        return dash.no_update, (refresh or 0)+1, conv.id

    except Exception as e:
        db.rollback()
        return html.Div(str(e), className="sga-alert sga-alert-danger"), dash.no_update, dash.no_update
    finally:
        db.close()


# ── Liste des conversations ──
@callback(
    Output("msg-conv-list","children"),
    Input("msg-refresh","data"),
    Input("msg-poll","n_intervals"),
    Input("msg-conv-id","data"),
    State("session-store","data"),
)
def render_conv_list(refresh, poll, active_id, session):
    if not session:
        return html.Div("Non connecte.", style={"padding":"16px","color":"var(--muted)"})
    uid = session.get("user_id")
    db  = SessionLocal()
    try:
        parts = db.query(ConvParticipant).filter_by(user_id=uid).all()
        conv_ids = [p.conversation_id for p in parts]
        lu_map   = {p.conversation_id: p.lu_at for p in parts}

        convs = []
        for cid in conv_ids:
            c = db.query(Conversation).get(cid)
            if not c:
                continue
            msgs  = c.messages
            last  = msgs[-1] if msgs else None
            nb_non_lu = sum(
                1 for m in msgs
                if m.sender_id != uid and
                (lu_map.get(cid) is None or
                 (m.created_at and lu_map.get(cid) and m.created_at > lu_map[cid]))
            )
            convs.append((c, last, nb_non_lu))

        convs.sort(key=lambda x: (x[1].created_at if x[1] else x[0].created_at), reverse=True)

        if not convs:
            return html.Div("Aucune conversation.", style={"padding":"24px","color":"var(--muted)",
                             "textAlign":"center","fontSize":"13px"})

        items = []
        for conv, last_msg, nb_nl in convs:
            is_active = (conv.id == active_id)
            badge = html.Span(str(nb_nl),
                              style={"background":"var(--gold)","color":"var(--bg-primary)",
                                     "borderRadius":"50%","width":"18px","height":"18px",
                                     "display":"flex","alignItems":"center","justifyContent":"center",
                                     "fontSize":"10px","fontWeight":"700","flexShrink":"0"}) \
                    if nb_nl > 0 else html.Div()

            preview = ""
            if last_msg:
                preview = last_msg.contenu[:60] + ("..." if len(last_msg.contenu) > 60 else "")

            items.append(html.Div([
                html.Div([
                    html.Div(conv.sujet,
                             style={"fontWeight":"700" if nb_nl > 0 else "600",
                                    "fontSize":"13px","marginBottom":"3px",
                                    "color":"var(--gold)" if is_active else "var(--text-primary)",
                                    "overflow":"hidden","textOverflow":"ellipsis","whiteSpace":"nowrap"}),
                    html.Div(preview, style={"fontSize":"11px","color":"var(--muted)",
                                             "overflow":"hidden","textOverflow":"ellipsis",
                                             "whiteSpace":"nowrap"}),
                ], style={"flex":"1","minWidth":"0"}),
                html.Div([
                    html.Div(last_msg.created_at.strftime("%d/%m %H:%M") if last_msg and last_msg.created_at else "",
                             style={"fontSize":"10px","color":"var(--muted)","marginBottom":"4px",
                                    "whiteSpace":"nowrap"}),
                    badge,
                ], style={"display":"flex","flexDirection":"column","alignItems":"flex-end",
                           "flexShrink":"0"}),
            ], id={"type":"conv-item","index":conv.id},
               n_clicks=0,
               style={"display":"flex","gap":"12px","padding":"14px 16px","cursor":"pointer",
                      "borderBottom":"1px solid var(--border)","alignItems":"center",
                      "background":"rgba(184,146,42,0.08)" if is_active else "transparent",
                      "transition":"background 0.15s"}))
        return html.Div(items)
    finally:
        db.close()


# ── Clic sur une conversation ──
@callback(
    Output("msg-conv-id","data"),
    Input({"type":"conv-item","index":dash.ALL},"n_clicks"),
    prevent_initial_call=True,
)
def select_conv(n_clicks):
    if not ctx.triggered_id or not isinstance(ctx.triggered_id, dict):
        return dash.no_update
    return ctx.triggered_id["index"]


# ── Afficher le fil ──
@callback(
    Output("msg-thread","children"),
    Input("msg-conv-id","data"),
    Input("msg-refresh","data"),
    Input("msg-poll","n_intervals"),
    State("session-store","data"),
)
def render_thread(conv_id, refresh, poll, session):
    if not conv_id or not session:
        return html.Div([
            html.Div("Selectionnez une conversation", style={
                "textAlign":"center","color":"var(--muted)","fontSize":"15px",
                "fontFamily":"Times New Roman,serif","marginTop":"80px"}),
            html.Div("ou creez-en une nouvelle",
                     style={"textAlign":"center","color":"var(--muted)","fontSize":"12px","marginTop":"8px"}),
        ])

    uid = session.get("user_id")
    db  = SessionLocal()
    try:
        conv = db.query(Conversation).get(conv_id)
        if not conv:
            return html.Div("Conversation introuvable.", style={"padding":"24px","color":"var(--muted)"})

        # Marquer comme lu
        part = db.query(ConvParticipant).filter_by(conversation_id=conv_id, user_id=uid).first()
        if part:
            part.lu_at = datetime.now()
            db.commit()

        # Participants
        parts = conv.participants
        noms  = []
        for p in parts:
            if p.user and p.user_id != uid:
                noms.append(p.user.username)
        participants_str = ", ".join(noms) if noms else "Vous seul"

        # Messages
        bulles = []
        for msg in conv.messages:
            is_me = (msg.sender_id == uid)
            sender_name = msg.sender.username if msg.sender else "?"
            sender_role = msg.sender.role if msg.sender else ""
            role_col    = ROLE_COLORS.get(sender_role, "var(--muted)")
            heure       = msg.created_at.strftime("%d/%m %H:%M") if msg.created_at else ""

            # Piece jointe
            pj_elem = html.Div()
            if msg.piece_jointe and msg.pj_nom:
                if msg.pj_type == "image":
                    pj_elem = html.Div([
                        html.Img(src=msg.piece_jointe,
                                 style={"maxWidth":"220px","maxHeight":"160px","borderRadius":"4px",
                                        "marginTop":"8px","display":"block"}),
                    ])
                else:
                    pj_elem = html.A([
                        html.Span("📎 ", style={"marginRight":"4px"}),
                        html.Span(msg.pj_nom, style={"textDecoration":"underline"}),
                    ], href=msg.piece_jointe, target="_blank",
                       style={"display":"block","marginTop":"8px","fontSize":"12px",
                              "color":"var(--gold)"})

            bulle = html.Div([
                html.Div([
                    html.Span(sender_name,
                              style={"fontSize":"11px","fontWeight":"700","color":role_col,
                                     "marginRight":"8px"}),
                    html.Span(ROLE_LABELS.get(sender_role,""),
                              style={"fontSize":"10px","color":"var(--muted)","marginRight":"8px"}),
                    html.Span(heure, style={"fontSize":"10px","color":"var(--muted)"}),
                ], style={"marginBottom":"5px",
                          "textAlign":"right" if is_me else "left"}),
                html.Div([
                    html.Div(msg.contenu,
                             style={"fontSize":"13px","lineHeight":"1.6","whiteSpace":"pre-wrap"}),
                    pj_elem,
                ], style={
                    "display":"inline-block","maxWidth":"70%","padding":"10px 14px",
                    "borderRadius":"12px 12px 4px 12px" if is_me else "12px 12px 12px 4px",
                    "background":"rgba(184,146,42,0.15)" if is_me else "var(--bg-secondary)",
                    "border":"1px solid var(--border)",
                }),
            ], style={"marginBottom":"16px",
                      "display":"flex","flexDirection":"column",
                      "alignItems":"flex-end" if is_me else "flex-start"})
            bulles.append(bulle)

        return html.Div([
            # En-tete
            html.Div([
                html.Div([
                    html.Div(conv.sujet, style={"fontWeight":"700","fontSize":"16px","marginBottom":"2px"}),
                    html.Div(f"Avec : {participants_str}",
                             style={"fontSize":"11px","color":"var(--muted)"}),
                ]),
                html.Span("GROUPE" if conv.type_conv == "groupe" else "PRIVE",
                          style={"fontSize":"9px","letterSpacing":"2px","fontWeight":"700",
                                 "color":"var(--gold)","border":"1px solid var(--gold)",
                                 "padding":"2px 8px","borderRadius":"2px"}),
            ], style={"display":"flex","justifyContent":"space-between","alignItems":"center",
                      "padding":"16px 20px","borderBottom":"1px solid var(--border)",
                      "flexShrink":"0"}),

            # Messages
            html.Div(bulles, id="msg-bulles",
                     style={"flex":"1","overflowY":"auto","padding":"20px",
                            "display":"flex","flexDirection":"column"}),

            # Zone de saisie
            html.Div([
                dcc.Upload(id="reply-upload",
                           children=html.Div("📎", style={"fontSize":"18px","cursor":"pointer",
                                             "padding":"8px","color":"var(--muted)"}),
                           style={"flexShrink":"0"},
                           max_size=5_000_000),
                dcc.Input(id="reply-text", placeholder="Ecrire un message...",
                          className="sga-input",
                          style={"flex":"1","marginBottom":"0"},
                          debounce=False,
                          n_submit=0),
                html.Button("Envoyer", id="btn-reply-send", n_clicks=0,
                            className="btn-sga btn-gold",
                            style={"flexShrink":"0","padding":"10px 20px"}),
                html.Div(id="reply-upload-name",
                         style={"fontSize":"10px","color":"var(--muted)","alignSelf":"center"}),
            ], style={"display":"flex","gap":"8px","padding":"12px 16px","alignItems":"center",
                      "borderTop":"1px solid var(--border)","flexShrink":"0"}),

            # Store upload en attente
            dcc.Store(id="reply-upload-data", data=None),
        ], style={"display":"flex","flexDirection":"column","height":"100%"})
    finally:
        db.close()


# ── Stocker la piece jointe de la reponse ──
@callback(
    Output("reply-upload-data","data"),
    Output("reply-upload-name","children"),
    Input("reply-upload","contents"),
    State("reply-upload","filename"),
    prevent_initial_call=True,
)
def store_upload(contents, filename):
    if not contents:
        return None, ""
    return {"contents":contents,"filename":filename}, f"📎 {filename}"


# ── Envoyer une reponse ──
@callback(
    Output("msg-refresh","data", allow_duplicate=True),
    Output("reply-text","value"),
    Output("reply-upload-data","data", allow_duplicate=True),
    Output("reply-upload-name","children", allow_duplicate=True),
    Input("btn-reply-send","n_clicks"),
    Input("reply-text","n_submit"),
    State("reply-text","value"),
    State("msg-conv-id","data"),
    State("reply-upload-data","data"),
    State("session-store","data"),
    State("msg-refresh","data"),
    prevent_initial_call=True,
)
def envoyer_reponse(n_btn, n_sub, texte, conv_id, upload_data, session, refresh):
    if not texte and not upload_data:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update
    if not conv_id or not session:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update

    sender_id = session.get("user_id")
    db = SessionLocal()
    try:
        pj_path = pj_nom = pj_type = None
        if upload_data:
            contents    = upload_data["contents"]
            filename    = upload_data["filename"]
            ext         = filename.rsplit(".",1)[-1].lower() if "." in filename else ""
            pj_type     = "pdf" if ext == "pdf" else "image" if ext in ("png","jpg","jpeg","gif","webp") else "fichier"
            fname       = f"{uuid.uuid4().hex[:12]}_{filename}"
            fpath       = os.path.join(UPLOAD_DIR, fname)
            content_str = contents.split(",")[1] if "," in contents else contents
            with open(fpath, "wb") as f:
                f.write(base64.b64decode(content_str))
            pj_path = f"/assets/uploads/{fname}"
            pj_nom  = filename

        msg = Message()
        msg.conversation_id = conv_id
        msg.sender_id       = sender_id
        msg.contenu         = texte or ""
        msg.piece_jointe    = pj_path
        msg.pj_nom          = pj_nom
        msg.pj_type         = pj_type
        msg.created_at      = datetime.now()
        db.add(msg)

        # Mettre a jour lu_at de l'expediteur
        part = db.query(ConvParticipant).filter_by(
            conversation_id=conv_id, user_id=sender_id).first()
        if part:
            part.lu_at = datetime.now()

        db.commit()
        return (refresh or 0)+1, "", None, ""
    except Exception as e:
        db.rollback()
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update
    finally:
        db.close()
