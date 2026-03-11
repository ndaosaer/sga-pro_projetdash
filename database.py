from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models import Base
from werkzeug.security import generate_password_hash

DATABASE_URL = "sqlite:///sga_pro.db"
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
    pool_size=10,          # connexions maintenues ouvertes
    max_overflow=20,       # connexions supplementaires si besoin
    pool_pre_ping=True,    # verifie la connexion avant usage
    pool_recycle=300,      # recycle les connexions apres 5 min
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def init_db():
    Base.metadata.create_all(bind=engine)
    # Migration : ajouter linked_id si absent
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN linked_id INTEGER"))
            conn.commit()
    except Exception:
        pass
    # Migration notifications — nouvelles colonnes
    for col_sql in [
        "ALTER TABLE notifications ADD COLUMN student_id INTEGER",
        "ALTER TABLE notifications ADD COLUMN destinataire TEXT",
        "ALTER TABLE notifications ADD COLUMN categorie TEXT",
    ]:
        try:
            with engine.connect() as conn:
                conn.execute(text(col_sql))
                conn.commit()
        except Exception:
            pass
    _seed_default_data()
    print("Base de donnees initialisee.")

def _seed_default_data():
    from models import (User, Student, Course, Notification,
                        Session as Sess, Attendance, Grade,
                        Niveau, Classe, CoursClasse, FraisScolarite,
                        Concours, Candidat)
    from datetime import date, datetime, timedelta
    import random
    random.seed(42)
    db = SessionLocal()
    try:
        # ── Guard ──
        if db.query(User).count() > 5:
            db.close()
            return

        # ── Comptes admin/secrétariat ──
        def add_user(username, pwd, role, linked_id=None):
            if not db.query(User).filter_by(username=username).first():
                u = User()
                u.username      = username
                u.password_hash = generate_password_hash(pwd)
                u.role          = role
                u.linked_id     = linked_id
                db.add(u)

        add_user("admin",        "admin123",  "admin")
        add_user("secretaire",   "sec123",    "secretary")
        add_user("demo.parent",  "parent123", "parent")
        add_user("demo.etudiant","etu2026",   "student")
        db.commit()

        # ── Niveaux ──
        niveaux_data = [
            ("Licence",  "L", 1),
            ("Master",   "M", 2),
            ("Doctorat", "D", 3),
        ]
        niveaux = {}
        for nom, abrev, ordre in niveaux_data:
            if not db.query(Niveau).filter_by(abrev=abrev).first():
                n = Niveau(nom=nom, abrev=abrev, ordre=ordre)
                db.add(n); db.flush()
                niveaux[abrev] = n.id
            else:
                niveaux[abrev] = db.query(Niveau).filter_by(abrev=abrev).first().id
        db.commit()

        # ── Classes ──
        classes_data = [
            ("L1 Statistique",        "L1-STAT", "L", "Statistique",            "2025-2026", "#B8922A"),
            ("L2 Statistique",        "L2-STAT", "L", "Statistique",            "2025-2026", "#8B6914"),
            ("L3 Statistique",        "L3-STAT", "L", "Statistique",            "2025-2026", "#D4A84B"),
            ("L3 Economie",           "L3-ECO",  "L", "Economie",               "2025-2026", "#5A5650"),
            ("M1 Statistique",        "M1-STAT", "M", "Statistique Appliquée",  "2025-2026", "#2D6A3F"),
            ("M2 Data Science",       "M2-DATA", "M", "Data Science",           "2025-2026", "#9B5E2A"),
        ]
        classes = {}
        for nom, code, niv_abrev, filiere, annee, couleur in classes_data:
            if not db.query(Classe).filter_by(code=code).first():
                cl = Classe(nom=nom, code=code, niveau_id=niveaux[niv_abrev],
                            filiere=filiere, annee=annee, couleur=couleur,
                            effectif_max=40, created_at=datetime.now())
                db.add(cl); db.flush()
                classes[code] = cl.id
            else:
                classes[code] = db.query(Classe).filter_by(code=code).first().id
        db.commit()

        # ── Enseignants ──
        profs = [
            ("prof.diallo",  "Pr. Ibrahima Diallo"),
            ("prof.ndiaye",  "Pr. Aminata Ndiaye"),
            ("prof.fall",    "Pr. Ousmane Fall"),
            ("prof.ba",      "Pr. Mariama Ba"),
            ("prof.sow",     "Pr. Cheikh Sow"),
            ("prof.kane",    "Pr. Fatou Kane"),
            ("prof.traore",  "Pr. Moussa Traore"),
            ("prof.sarr",    "Pr. Rokhaya Sarr"),
            ("prof.diouf",   "Pr. Lamine Diouf"),
            ("prof.mbaye",   "Pr. Ndéye Mbaye"),
        ]
        for uname, _ in profs:
            add_user(uname, "prof2026", "teacher")
        db.commit()

        # ── Cours ──
        cours_data = [
            ("STAT101", "Statistique Descriptive",    60, "Pr. Ibrahima Diallo",  "#B8922A", "prof.diallo", "L1-STAT"),
            ("MATH101", "Mathématiques pour Stats",   45, "Pr. Aminata Ndiaye",   "#8B6914", "prof.ndiaye", "L1-STAT"),
            ("INFO101", "Informatique Statistique",   40, "Pr. Ousmane Fall",     "#2D6A3F", "prof.fall",   "L1-STAT"),
            ("STAT201", "Probabilités",               60, "Pr. Ibrahima Diallo",  "#B8922A", "prof.diallo", "L2-STAT"),
            ("ECO201",  "Econométrie",                45, "Pr. Cheikh Sow",       "#5A5650", "prof.sow",    "L2-STAT"),
            ("STAT301", "Inférence Statistique",      60, "Pr. Mariama Ba",       "#D4A84B", "prof.ba",     "L3-STAT"),
            ("ECO301",  "Macroéconomie",              45, "Pr. Fatou Kane",       "#9B5E2A", "prof.kane",   "L3-ECO"),
            ("STAT401", "Séries Temporelles",         60, "Pr. Moussa Traore",    "#B8922A", "prof.traore", "M1-STAT"),
            ("ML501",   "Machine Learning",           60, "Pr. Ousmane Fall",     "#2D6A3F", "prof.fall",   "M2-DATA"),
            ("DATA501", "Big Data & Visualisation",   45, "Pr. Rokhaya Sarr",     "#8B6914", "prof.sarr",   "M2-DATA"),
            ("LANG101", "Anglais Scientifique",       30, "Pr. Ndéye Mbaye",      "#5A5650", "prof.mbaye",  "L1-STAT"),
            ("METH301", "Méthodes d'Enquête",         40, "Pr. Lamine Diouf",     "#9B5E2A", "prof.diouf",  "L3-STAT"),
            ("ECO401",  "Economie du Développement",  45, "Pr. Cheikh Sow",       "#5A5650", "prof.sow",    "M1-STAT"),
        ]
        for code, lib, vol, ens, col, tuname, classe_code in cours_data:
            if not db.query(Course).filter_by(code=code).first():
                c = Course(code=code, libelle=lib, volume_horaire=vol,
                           enseignant=ens, couleur=col, teacher_username=tuname)
                db.add(c); db.flush()
                if classe_code in classes:
                    cc = CoursClasse(course_code=code, classe_id=classes[classe_code],
                                     enseignant=tuname, created_at=datetime.now())
                    db.add(cc)
        db.commit()

        # ── 60 Étudiants sénégalais ──
        prenoms_m = ["Ibrahima","Cheikh","Moussa","Ousmane","Lamine","Mamadou","Abdoulaye",
                     "Modou","Samba","Pape","Omar","Seydou","Boubacar","Idrissa","Serigne"]
        prenoms_f = ["Fatou","Aminata","Mariama","Rokhaya","Ndéye","Aissatou","Khady",
                     "Coumba","Adja","Mame","Yacine","Astou","Sokhna","Dieynaba","Binta"]
        noms = ["Diallo","Ndiaye","Fall","Ba","Sow","Kane","Traore","Sarr","Diouf","Mbaye",
                "Gueye","Diop","Faye","Thiam","Cissé","Ndour","Badji","Camara","Koné","Seck"]

        classes_list = list(classes.keys())
        random.seed(42)
        etudiants_crees = []
        used_emails = set()
        count = 0
        random.shuffle(prenoms_m); random.shuffle(prenoms_f)
        all_prenoms = [(p, "M") for p in prenoms_m*3] + [(p, "F") for p in prenoms_f*3]
        random.shuffle(all_prenoms)

        for i in range(60):
            prenom, genre = all_prenoms[i % len(all_prenoms)]
            nom = noms[i % len(noms)]
            email_base = f"{prenom.lower().replace('é','e').replace('è','e').replace('ê','e').replace('ndé','nde')}.{nom.lower()}@ensae.sn"
            email = email_base
            suffix = 1
            while email in used_emails:
                email = f"{prenom.lower()}{suffix}.{nom.lower()}@ensae.sn"
                suffix += 1
            used_emails.add(email)

            annee_nais = 1999 + (i % 5)
            mois_nais  = 1 + (i % 12)
            jour_nais  = 1 + (i % 28)
            classe_code = classes_list[i % len(classes_list)]

            stu = Student(
                nom=nom.upper(), prenom=prenom,
                email=email,
                date_naissance=date(annee_nais, mois_nais, jour_nais),
                classe_id=classes[classe_code],
                actif=True,
                created_at=datetime.now()
            )
            db.add(stu); db.flush()
            etudiants_crees.append(stu)

            uname = f"{prenom.lower().replace('é','e').replace('è','e').replace('ê','e').replace('ndé','nde')}.{nom.lower()}"
            if suffix > 1: uname += str(suffix-1)
            add_user(uname, "etu2026", "student", linked_id=stu.id)

            # Frais scolarité
            montant = 450000 if classe_code.startswith("M") else 350000
            frais = FraisScolarite(
                student_id=stu.id, annee="2025-2026",
                montant_total=montant, created_at=datetime.now()
            )
            db.add(frais)

        db.commit()

        # ── Cours, notes, présences ──
        courses = db.query(Course).all()
        today   = date.today()
        random.seed(42)

        for course in courses:
            for i in range(random.randint(5, 10)):
                sess = Sess(
                    course_code=course.code,
                    date=today - timedelta(days=random.randint(1, 90)),
                    duree=random.choice([1.5, 2.0, 2.5, 3.0]),
                    theme=f"Séance {i+1}"
                )
                db.add(sess); db.flush()
                for stu in etudiants_crees:
                    if random.random() < 0.10:
                        db.add(Attendance(id_session=sess.id, id_student=stu.id))

        for stu in etudiants_crees:
            for course in courses:
                if random.random() > 0.12:
                    note_base = random.gauss(13.5, 3.5)
                    note = round(max(0, min(20, note_base)), 2)
                    db.add(Grade(
                        id_student=stu.id, course_code=course.code,
                        note=note, coefficient=random.choice([1.0, 1.5, 2.0])
                    ))
        db.commit()

        # ── Concours ──
        if not db.query(Concours).first():
            con = Concours(
                nom="Concours ENSAE 2026",
                annee="2026",
                description="Concours national d'admission à l'ENSAE",
                date_ouverture=date(2026, 1, 15),
                date_cloture=date(2026, 4, 30),
                date_epreuve=date(2026, 5, 15),
                date_resultats=date(2026, 6, 1),
                frais_dossier=15000,
                actif=True,
                created_at=datetime.now()
            )
            db.add(con); db.flush()

        # ── Notifications ──
        db.add(Notification(type="success", titre="Base initialisée",
            message="60 étudiants, 10 enseignants et 13 cours chargés."))
        db.add(Notification(type="info", titre="Concours ouvert",
            message="Le concours ENSAE 2026 est ouvert aux candidatures."))
        db.add(Notification(type="warning", titre="Rappel paiements",
            message="Certains étudiants n'ont pas encore réglé leur scolarité."))
        db.commit()
        print(f"✓ Base peuplée : {len(etudiants_crees)} étudiants, {len(courses)} cours")

    except Exception as e:
        db.rollback()
        print(f"Seed error: {e}")
        import traceback; traceback.print_exc()
    finally:
        db.close()
def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

if __name__ == "__main__":
    init_db()


def init_users():
    """Crée les comptes par défaut si la table users est vide."""
    from werkzeug.security import generate_password_hash
    from models import User
    from datetime import datetime
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            defaults = [
                ("admin",         "admin123",  "admin",     None),
                ("secretaire",    "sec123",    "secretary", None),
                ("demo.parent",   "parent123", "parent",    None),
                ("demo.etudiant", "etu2026",   "student",   None),
                ("prof.diallo",   "prof2026",  "teacher",   None),
            ]
            for username, pwd, role, linked_id in defaults:
                u = User()
                u.username = username
                u.password_hash = generate_password_hash(pwd)
                u.role = role
                u.linked_id = linked_id
                u.created_at = datetime.now()
                db.add(u)
            db.commit()
            print(" Comptes par défaut créés.")
    finally:
        db.close()
