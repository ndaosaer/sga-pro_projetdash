import dash
from dash import html, dcc

dash.register_page(__name__, path="/paiement-annule", name="Paiement annulé")


def layout():
    return html.Div([
        html.Div([
            html.Div("✗", style={
                "fontSize":"64px","color":"var(--red)","marginBottom":"16px","lineHeight":"1"}),
            html.Div("Paiement annulé", style={
                "fontFamily":"Times New Roman,serif","fontSize":"32px",
                "fontWeight":"700","color":"var(--red)","marginBottom":"8px"}),
            html.Div("Votre paiement a été annulé. Aucun montant n'a été débité.",
                     style={"fontSize":"14px","color":"var(--muted)","marginBottom":"32px"}),
            dcc.Link("← Réessayer", href="/paiement-en-ligne",
                     style={"color":"var(--gold)","textDecoration":"none",
                            "fontWeight":"600","fontSize":"13px"}),
        ], style={
            "maxWidth":"440px","margin":"120px auto","textAlign":"center",
            "padding":"48px","background":"var(--bg-card)",
            "border":"1px solid rgba(139,37,0,0.2)","borderRadius":"6px",
        }),
    ])
