# SGA Pro — Systeme de Gestion Academique

SGA Pro est une application web de gestion academique destinee aux etablissements
scolaires prives, universites et centres de formation. Elle centralise la gestion
des cours, des etudiants, des presences, des notes et des bulletins dans une
interface unique, accessible depuis n'importe quel navigateur, sans connexion
internet permanente requise.

---

## Sommaire

1. Prerequis
2. Installation
3. Lancement
4. Comptes par defaut
5. Structure du projet
6. Modules de l'application
7. Systeme de roles
8. Base de donnees
9. Scripts d'installation
10. Deploiement sur GitHub

---

## 1. Prerequis

- Python 3.10 ou superieur (teste avec Python 3.12)
- pip
- Un navigateur web moderne (Chrome, Firefox, Edge)
- Windows, macOS ou Linux

---

## 2. Installation

Cloner le depot ou extraire l'archive, puis installer les dependances :

```bash
pip install dash==2.17.1
pip install dash-bootstrap-components==1.6.0
pip install plotly==5.22.0
pip install sqlalchemy==2.0.30
pip install pandas==2.2.2
pip install openpyxl==3.1.2
pip install werkzeug==3.0.6
pip install reportlab
```

Ou en une seule commande depuis le dossier du projet :

```bash
pip install -r requirements.txt
```

---

## 3. Lancement

```bash
cd sga_pro
python app.py
```

L'application s'ouvre automatiquement dans le navigateur sur :

```
http://127.0.0.1:8050/accueil
```

La base de donnees SQLite est creee automatiquement au premier lancement dans
le fichier `sga_pro.db`. Les comptes par defaut sont egalement crees
automatiquement si la table utilisateurs est vide.

---

## 4. Comptes par defaut

Ces comptes sont crees automatiquement au premier lancement.

| Identifiant | Mot de passe | Role         | Acces                          |
|-------------|-------------|--------------|-------------------------------|
| admin       | admin123    | Directeur    | Tous les modules               |
| enseignant  | teach123    | Enseignant   | Ses cours et etudiants         |
| secretaire  | secr123     | Secretaire   | Etudiants, cours, presences    |
| etudiant    | etu123      | Etudiant     | Ses notes et bulletin          |
| parent      | parent123   | Parent       | Resultats de son enfant        |

Pour creer d'autres comptes, connectez-vous en tant qu'admin et accedez a la
page Gestion des comptes (`/gestion-comptes`).

Pour reinitialiser les comptes de demonstration, utiliser le script :

```powershell
PowerShell -ExecutionPolicy Bypass -File "RESET_comptes_demo.ps1"
```

---

## 5. Structure du projet

```
Projet_final_Dash/
    sga_pro/
        app.py                  Point d'entree, routage, protection des pages
        models.py               Modeles SQLAlchemy (User, Student, Course...)
        database.py             Initialisation DB, seed des donnees
        requirements.txt        Dependances Python
        sga_pro.db              Base SQLite (generee automatiquement)
        pages/
            accueil.py          Page d'accueil vitrine
            auth.py             Connexion et inscription
            dashboard.py        Tableau de bord principal
            module1_cours.py    Gestion des cours
            module2_presences.py  Gestion des presences et notes
            module3_etudiants.py  Fiches etudiants
            analytics.py        Graphiques et statistiques avancees
            appel_rapide.py     Appel en mode rapide
            alertes.py          Systeme d'alertes intelligentes
            bulletin.py         Generation de bulletins PDF
            calendrier.py       Calendrier des seances
            comparateur.py      Comparateur de cours et d'etudiants
            portail_etudiant.py Espace personnel etudiant
            portail_parent.py   Espace suivi parent
            portail_secretaire.py Interface secretariat
            gestion_comptes.py  Administration des comptes (admin)
        components/
            sidebar.py          Menu lateral dynamique selon le role
        assets/
            style.css           Styles globaux (theme Or / Parchemin)
            landing.css         Styles specifiques a la page d'accueil
```

---

## 6. Modules de l'application

### Page d'accueil (`/accueil`)

Vitrine de l'application presentant le produit, ses fonctionnalites, les
tarifs et un formulaire de contact. Accessible sans connexion.

### Connexion (`/auth`)

Page de connexion avec selection visuelle du role (5 boutons), formulaire
identifiant / mot de passe, et onglet inscription pour creer un nouveau compte.

### Dashboard (`/`)

Vue d'ensemble en temps reel : nombre d'etudiants, de cours, de seances, moyenne
generale de la promotion. Acces rapide aux alertes et aux derniers evenements.

### Gestion des cours (`/cours`)

Creation, modification et suppression des matieres. Chaque cours possede un code
unique, un volume horaire, un enseignant responsable et une couleur d'identification.

### Presences et notes (`/presences`)

Saisie des notes par cours avec coefficient. Consultation des presences par seance.
Calcul automatique des moyennes ponderees.

### Fiches etudiants (`/etudiants`)

Liste complete des etudiants avec profil individuel : radar de competences, historique
des notes, taux d'absence calcule automatiquement, statut actif / inactif.

### Appel rapide (`/appel`)

Interface optimisee pour faire l'appel en moins de 10 secondes. Cartes cliquables
representant chaque etudiant, boutons "Tout present" et "Tout absent", validation en
un clic qui cree la seance et enregistre les absences en base.

### Alertes intelligentes (`/alertes`)

Detection automatique de trois types de situations :
- Taux d'absence superieur au seuil configure (defaut 20%)
- Moyenne inferieure au seuil configure (defaut 10/20)
- Cours sans seance depuis plus de 14 jours

Les seuils sont configurables depuis l'interface. Les alertes sont classees par
niveau de gravite (critique / attention) et sauvegardees dans la table notifications.

### Bulletins PDF (`/bulletin`)

Generation de bulletins au format PDF avec le theme graphique de l'application.
Chaque bulletin contient les notes par matiere avec codes couleur, la moyenne
generale, la mention et un champ d'appreciation libre. Export individuel ou
archive ZIP pour toute la promotion.

### Calendrier (`/calendrier`)

Vue mensuelle des seances avec navigation entre les mois. Chaque jour affiche
les seances du jour sous forme de pastilles colorees par cours. Clic sur un jour
pour voir le detail. Formulaire de planification de nouvelle seance integre.

### Comparateur (`/comparateur`)

Comparaison cote a cote de deux cours ou de deux etudiants. Affichage de 6
indicateurs cles avec mise en evidence du meilleur resultat, graphique radar
superpose pour les profils academiques, histogramme groupe par matiere.

### Analytics (`/analytics`)

Tableaux de bord avancee : violin plot de la distribution des notes, scatter plot
absences versus notes, timeline de progression, repartition des mentions. Filtrable
par cours et par periode.

### Espace etudiant (`/portail-etudiant`)

Interface personnelle accessible uniquement avec un compte de role etudiant. Affiche
les notes de l'etudiant connecte, son profil radar, son taux d'absence et sa moyenne
generale avec mention.

### Espace parent (`/portail-parent`)

Consultation des resultats de l'enfant lie au compte parent. Affiche les alertes
actives (moyenne insuffisante, absences excessives), le tableau des notes par
matiere et les informations du profil.

### Espace secretariat (`/portail-secretaire`)

Interface en 4 onglets : liste des etudiants inscrits, catalogue des cours,
historique des presences sur les 30 dernieres seances, calendrier des prochaines
seances planifiees. Acces en lecture seule aux notes.

### Gestion des comptes (`/gestion-comptes`)

Accessible uniquement au role admin. Creation de nouveaux comptes avec choix
du role et liaison optionnelle a un etudiant (pour les roles etudiant et parent).
Liste de tous les comptes existants avec leur role et leur statut.

---

## 7. Systeme de roles

L'application gere 5 roles distincts. Le role est stocke en base de donnees
et determine automatiquement l'interface affichee apres connexion.

### Admin (Directeur)

Acces complet a tous les modules. Seul role pouvant acceder a `/gestion-comptes`
pour creer et gerer les comptes utilisateurs. Voit la sidebar complete avec les
sections Navigation, Outils et Admin.

### Teacher (Enseignant)

Acces au dashboard, a ses cours, a ses etudiants, a l'appel rapide, aux bulletins,
au calendrier et aux alertes. La sidebar affiche uniquement les modules pertinents.
En theorie, un enseignant ne devrait voir que ses propres cours (filtrage par
`teacher_username` dans la table courses).

### Secretary (Secretaire)

Redirige vers `/portail-secretaire` apres connexion. Interface dediee sans sidebar.
Consultation des etudiants, cours et presences. Ne peut pas saisir de notes.

### Student (Etudiant)

Redirige vers `/portail-etudiant` apres connexion. Ne voit que ses propres donnees.
Le champ `linked_id` du compte utilisateur doit pointer vers l'`id` de la table
`students` pour afficher les bonnes informations.

### Parent

Redirige vers `/portail-parent` apres connexion. Ne voit que les resultats de
l'enfant dont l'`id` est dans le champ `linked_id` du compte utilisateur.

### Protection des routes

Chaque route est protegee dans `app.py` via le dictionnaire `ROLE_ROUTES`. Une
tentative d'acces a une route non autorisee affiche un message d'erreur et un
lien de retour. Les routes publiques (accueil, auth) ne necessitent pas de
connexion.

---

## 8. Base de donnees

La base de donnees est SQLite, stockee dans `sga_pro/sga_pro.db`. Elle est
geree via SQLAlchemy 2.0 en mode ORM.

### Table users

| Colonne       | Type    | Description                              |
|---------------|---------|------------------------------------------|
| id            | Integer | Cle primaire                             |
| username      | String  | Identifiant unique de connexion          |
| password_hash | String  | Mot de passe hache (Werkzeug PBKDF2)     |
| role          | String  | admin, teacher, student, parent, secretary |
| linked_id     | Integer | Lien vers students.id (etudiant/parent)  |
| created_at    | DateTime | Date de creation                        |

### Table students

| Colonne        | Type    | Description              |
|----------------|---------|--------------------------|
| id             | Integer | Cle primaire             |
| nom            | String  | Nom de famille           |
| prenom         | String  | Prenom                   |
| email          | String  | Adresse email unique     |
| date_naissance | Date    | Date de naissance        |
| actif          | Boolean | Etudiant actif ou non    |
| created_at     | DateTime | Date d'inscription      |

### Table courses

| Colonne          | Type   | Description                        |
|------------------|--------|------------------------------------|
| code             | String | Cle primaire (ex: MATH01)          |
| libelle          | String | Intitule complet de la matiere     |
| volume_horaire   | Float  | Volume horaire total               |
| enseignant       | String | Nom de l'enseignant responsable    |
| teacher_username | String | Username du compte enseignant      |
| couleur          | String | Code couleur hexadecimal           |
| description      | Text   | Description optionnelle            |

### Table sessions

| Colonne     | Type    | Description                         |
|-------------|---------|-------------------------------------|
| id          | Integer | Cle primaire                        |
| course_code | String  | Cle etrangere vers courses          |
| date        | Date    | Date de la seance                   |
| duree       | Float   | Duree en heures                     |
| theme       | String  | Intitule ou theme de la seance      |
| objectifs   | Text    | Objectifs pedagogiques              |

### Table attendance

| Colonne    | Type    | Description                              |
|------------|---------|------------------------------------------|
| id_session | Integer | Cle etrangere vers sessions              |
| id_student | Integer | Cle etrangere vers students              |
| justifiee  | Boolean | Absence justifiee ou non                 |

Cle primaire composite (id_session, id_student). Un enregistrement signifie
que l'etudiant etait ABSENT a cette seance.

### Table grades

| Colonne     | Type    | Description                         |
|-------------|---------|-------------------------------------|
| id          | Integer | Cle primaire                        |
| id_student  | Integer | Cle etrangere vers students         |
| course_code | String  | Cle etrangere vers courses          |
| note        | Float   | Note sur 20                         |
| coefficient | Float   | Coefficient de la matiere           |
| commentaire | Text    | Commentaire optionnel               |

Contrainte d'unicite sur (id_student, course_code) : une seule note par
etudiant par cours.

### Table notifications

| Colonne    | Type    | Description                              |
|------------|---------|------------------------------------------|
| id         | Integer | Cle primaire                             |
| type       | String  | absence, moyenne, inactivite             |
| titre      | String  | Titre court de l'alerte                  |
| message    | Text    | Description complete                     |
| lu         | Boolean | Notification lue ou non                  |
| created_at | DateTime | Date de creation                        |

---

## 9. Scripts d'installation

Tous les scripts PowerShell se placent dans `Projet_final_Dash\` et s'executent
avec la commande :

```powershell
PowerShell -ExecutionPolicy Bypass -File "NOM_DU_SCRIPT.ps1"
```

| Script                    | Role                                                        |
|---------------------------|-------------------------------------------------------------|
| INSTALL_SGA_PRO.ps1       | Installation complete initiale                              |
| AJOUT_appel_rapide.ps1    | Ajout du module Appel Rapide                                |
| AJOUT_alertes.ps1         | Ajout du systeme d'alertes                                  |
| AJOUT_bulletins.ps1       | Ajout de la generation PDF                                  |
| AJOUT_calendrier.ps1      | Ajout du calendrier des seances                             |
| AJOUT_comparateur.ps1     | Ajout du comparateur                                        |
| AJOUT_accueil.ps1         | Ajout de la page d'accueil vitrine                          |
| AJOUT_auth_roles.ps1      | Ajout du systeme d'authentification 5 roles                 |
| RESET_comptes_demo.ps1    | Reinitialisation des comptes de demonstration              |
| FIX_seed_error.ps1        | Correction erreur linked_id dans database.py               |
| FIX_page_connexion.ps1    | Correction page de connexion                               |

---

## 10. Deploiement sur GitHub

Voir le fichier `GITHUB_GUIDE.md` pour les instructions detaillees.

---

## Licence

Projet prive — tous droits reserves.

---

## Contact

contact@sgapro.io
