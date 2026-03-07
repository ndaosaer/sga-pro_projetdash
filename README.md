# SGA Pro — Système de Gestion Académique

> Plateforme académique complète pour les universités et grandes écoles d'Afrique de l'Ouest.  
> 23 modules · Python/Dash · Paiements Paytech · Déployé sur Railway

---

## Table des matières

1. [Présentation](#présentation)
2. [Fonctionnalités](#fonctionnalités)
3. [Rôles utilisateurs](#rôles-utilisateurs)
4. [Architecture](#architecture)
5. [Installation locale](#installation-locale)
6. [Comptes par défaut](#comptes-par-défaut)
7. [Paiements Paytech](#paiements-paytech)
8. [Déploiement Railway](#déploiement-railway)
9. [Variables d'environnement](#variables-denvironnement)
10. [Structure des fichiers](#structure-des-fichiers)
11. [Base de données](#base-de-données)

---

## Présentation

SGA Pro est une application web full-stack développée en **Python + Dash (Plotly)** qui centralise l'ensemble des opérations académiques d'un établissement d'enseignement supérieur :

- Gestion des étudiants, enseignants, cours, classes et niveaux
- Présences en temps réel, notes et moyennes automatiques
- Concours d'admission public avec paiement en ligne
- Facturation scolarité avec Wave, Orange Money, Free Money et Carte bancaire
- Tableaux de bord analytiques, messagerie interne, rapports PDF exportables
- Emploi du temps visuel avec détection de conflits

**Thème visuel :** Obsidian Gold × Parchemin — sidebar sombre, typographie Times New Roman + JetBrains Mono.

---

## Fonctionnalités

### Académique

| Module | Description | Rôles |
|--------|-------------|-------|
| Tableau de bord | KPIs, alertes, notifications temps réel | Admin |
| Gestion étudiants | Dossiers, import CSV, filtres, export | Admin, Secrétariat |
| Gestion enseignants | Profils, cours affectés, stats | Admin |
| Classes & Niveaux | Organisation L/M/D, filières, affectations | Admin |
| Emploi du temps | Grille visuelle, conflits, export PDF | Admin, Enseignant |
| Appel rapide | Saisie présences en moins de 10 secondes | Enseignant |
| Notes & Moyennes | Saisie, calcul automatique, classements | Enseignant |
| Analytics | Graphiques Plotly, tendances, comparaisons | Admin |
| Rapports PDF | Académique, financier, concours | Admin |

### Admission & Finance

| Module | Description | Rôles |
|--------|-------------|-------|
| Portail concours | Candidature publique sans connexion | Public |
| Admin concours | Gestion candidats, admissions, classements | Admin |
| Scolarité | Frais, paiements, relances, historique | Secrétariat |
| Paiement en ligne | Wave / Orange Money / Free Money / Carte | Public, Étudiant |

### Communication

| Module | Description | Rôles |
|--------|-------------|-------|
| Messagerie interne | Échanges entre tous les rôles | Tous |
| Notifications | Alertes temps réel dans la sidebar | Tous |

---

## Rôles utilisateurs

| Rôle | Description |
|------|-------------|
| `admin` | Accès complet à tous les modules et la configuration |
| `teacher` | Appel rapide, notes, emploi du temps de ses cours |
| `student` | Ses notes, son emploi du temps, sa scolarité |
| `secretary` | Étudiants, scolarité, concours |
| `parent` | Résultats et absences de son enfant |

---

## Architecture

```
sga_pro/
├── app.py                  # Point d'entrée, routes, webhook Paytech
├── models.py               # 13 tables SQLAlchemy
├── database.py             # Session, init, seed
├── peupler_base.py         # 60 étudiants, 10 profs, 6 classes
├── requirements.txt
├── Procfile                # gunicorn Railway
├── railway.toml
├── components/
│   └── sidebar.py
└── pages/                  # 23 modules Dash
    ├── accueil.py
    ├── login.py
    ├── dashboard.py
    ├── portail_concours.py  # Public — paiement Paytech intégré
    ├── paiement_en_ligne.py
    ├── emploi_du_temps.py
    ├── gestion_classes.py
    ├── rapports.py
    └── ...
```

### Stack

| Couche | Technologie |
|--------|-------------|
| Framework | Dash 2.14 + Flask |
| ORM | SQLAlchemy 2.0 |
| Base de données | SQLite / PostgreSQL |
| PDF | ReportLab |
| Serveur prod | Gunicorn |
| Paiements | Paytech API |
| Déploiement | Railway.app |
| Auth | Werkzeug scrypt |

---

## Installation locale

```bash
# 1. Se placer dans le dossier projet
cd sga_pro

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Peupler la base (60 étudiants, 10 profs, 6 classes)
python peupler_base.py

# 4. Lancer
python app.py
# → http://localhost:8050
```

---

## Comptes par défaut

| Identifiant | Mot de passe | Rôle |
|-------------|--------------|------|
| `admin` | `admin123` | Administrateur |
| `secretaire` | `sec123` | Secrétariat |
| `prof.diallo` | `prof2026` | Enseignant |
| `prof.ndiaye` | `prof2026` | Enseignant |
| `fatou.diallo` | `etu2026` | Étudiant |
| *(60 étudiants)* | `etu2026` | Étudiant |

---

## Paiements Paytech

### Moyens acceptés
-  Wave (Sénégal, CI)
-  Orange Money (SN, CI, ML, BF)
-  Free Money (Sénégal)
-  Carte bancaire Visa / Mastercard

### Flux
```
Utilisateur → SGA Pro → Paytech API → Checkout mobile
Paytech → Webhook /webhook/paytech → Base mise à jour
Paytech → Redirect /paiement-succes
```

### Activer en production

Variables Railway à configurer :
```
PAYTECH_API_KEY    = votre_cle
PAYTECH_API_SECRET = votre_secret
PAYTECH_ENV        = prod
APP_URL            = https://votre-app.up.railway.app
```

> Compte marchand Paytech requis. Inscription sur paytech.sn avec NINEA + documents établissement.

---

## Déploiement Railway

```bash
# Dans le dossier sga_pro
git init
git add .
git commit -m "SGA Pro v1.0"

# Pousser sur GitHub
git remote add origin https://github.com/USER/sga-pro.git
git push -u origin main
```

Puis sur [railway.app](https://railway.app) :
1. **New Project** → **Deploy from GitHub repo**
2. Sélectionner le repo
3. Railway détecte Python et lit le `Procfile`
4. En ligne en ~2 minutes avec URL HTTPS

**Volume persistant (base de données) :**  
Railway → Settings → Add Volume → Mount path : `/app/sga_pro`

---

## Variables d'environnement

| Variable | Description |
|----------|-------------|
| `PAYTECH_API_KEY` | Clé API Paytech |
| `PAYTECH_API_SECRET` | Secret Paytech |
| `PAYTECH_ENV` | `prod` ou `test` |
| `APP_URL` | URL publique Railway |
| `PORT` | Géré automatiquement par Railway |

---

## Base de données

13 tables principales :

`users` · `students` · `courses` · `sessions` · `attendance` · `grades` ·
`niveaux` · `classes` · `cours_classes` · `creneaux` · `frais_scolarite` ·
`paiements` · `concours` · `candidats` · `notifications` · `messages`

---

## Licence

© 2026 SGA Pro — Tous droits réservés.  
Développé pour usage académique institutionnel en Afrique de l'Ouest.
