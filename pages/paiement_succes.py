"""
SGA Pro — Webhook Paytech + pages succès/annulation
"""
import dash, json
from dash import html, dcc
from database import SessionLocal
from models import Paiement, Candidat, Student, FraisScolarite
from datetime import datetime
import flask

dash.register_page(__name__, path="/paiement-succes", name="Paiement réussi")


def layout():
    return html.Div([
        html.Div([
            html.Div("✓", style={
                "fontSize":"64px","color":"var(--green)","marginBottom":"16px",
                "lineHeight":"1"}),
            html.Div("Paiement confirmé", style={
                "fontFamily":"Times New Roman,serif","fontSize":"32px",
                "fontWeight":"700","color":"var(--green)","marginBottom":"8px"}),
            html.Div("Votre paiement a été enregistré avec succès.",
                     style={"fontSize":"14px","color":"var(--muted)","marginBottom":"32px"}),
            html.Div("Un email de confirmation a été envoyé à votre adresse.",
                     style={"fontSize":"13px","color":"var(--muted)","marginBottom":"32px",
                            "padding":"16px","background":"rgba(45,106,63,0.06)",
                            "border":"1px solid rgba(45,106,63,0.2)","borderRadius":"4px"}),
            html.Div([
                dcc.Link("← Retour à l'accueil", href="/accueil",
                         style={"color":"var(--gold)","textDecoration":"none",
                                "fontWeight":"600","fontSize":"13px","marginRight":"24px"}),
                dcc.Link("Mon espace étudiant", href="/portail-etudiant",
                         style={"color":"var(--muted)","textDecoration":"none","fontSize":"13px"}),
            ]),
        ], style={
            "maxWidth":"480px","margin":"120px auto","textAlign":"center",
            "padding":"48px","background":"var(--bg-card)",
            "border":"1px solid rgba(45,106,63,0.3)","borderRadius":"6px",
        }),
    ])
