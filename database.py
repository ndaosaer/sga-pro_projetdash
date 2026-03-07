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
    _seed_default_data()
    print("Base de donnees initialisee.")

def _seed_default_data():
    from models import User, Student, Course, Notification
    from datetime import date
    import random
    db = SessionLocal()
    try:
        # ── Guard : si la DB a deja ete peuplee, on ne refait rien ──────
        if db.query(User).count() > 5:
            db.close()
            return  # base deja initialisee, on saute tout le seed

        # ── Comptes utilisateurs ──────────────────────────────────────────
        def add_user(username, pwd, role, linked_id=None):
            if not db.query(User).filter_by(username=username).first():
                u = User()
                u.username = username
                u.password_hash = generate_password_hash(pwd)
                u.role = role
                u.linked_id = linked_id
                db.add(u)

        add_user("admin",     "admin123",  "admin")
        add_user("rousseau",  "prof123",   "teacher")
        add_user("blanc",     "prof123",   "teacher")
        add_user("secretaire","sec123",    "secretary")
        db.commit()

        # ── Étudiants ─────────────────────────────────────────────────────
        if db.query(Student).count() == 0:
            etudiants = [
                ("Dupont","Alice","alice@edu.fr",2002,3,15),
                ("Martin","Bob","bob@edu.fr",2001,7,22),
                ("Bernard","Clara","clara@edu.fr",2002,11,8),
                ("Petit","David","david@edu.fr",2001,5,30),
                ("Leroy","Emma","emma@edu.fr",2003,1,12),
                ("Moreau","Felix","felix@edu.fr",2002,9,4),
                ("Simon","Grace","grace@edu.fr",2001,12,19),
                ("Laurent","Hugo","hugo@edu.fr",2003,6,27),
            ]
            for nom,prenom,email,y,m,d in etudiants:
                db.add(Student(nom=nom,prenom=prenom,email=email,
                               date_naissance=date(y,m,d)))
            db.commit()

        # Créer comptes étudiants et parents liés
        students = db.query(Student).all()
        for stu in students:
            uname = f"{stu.prenom.lower()}.{stu.nom.lower()}"
            add_user(uname, "etudiant123", "student", linked_id=stu.id)
            parent_uname = f"parent.{stu.nom.lower()}"
            add_user(parent_uname, "parent123", "parent", linked_id=stu.id)
        db.commit()

        # ── Cours ─────────────────────────────────────────────────────────
        if db.query(Course).count() == 0:
            for code,lib,vol,ens,col,teacher in [
                ("MATH101","Mathématiques Avancées",60,"Dr. Rousseau","#B8922A","rousseau"),
                ("INFO202","Algorithmique",45,"Prof. Blanc","#2D6A3F","blanc"),
                ("PHYS101","Physique Quantique",40,"Dr. Rousseau","#9B5E2A","rousseau"),
                ("LANG301","Anglais Scientifique",30,"Prof. Blanc","#8B6914","blanc"),
            ]:
                db.add(Course(code=code,libelle=lib,volume_horaire=vol,
                              enseignant=ens,couleur=col,teacher_username=teacher))
            db.commit()

        from models import Session as Sess, Attendance, Grade
        from datetime import timedelta
        if db.query(Sess).count() == 0:
            courses  = db.query(Course).all()
            today    = date.today()
            for course in courses:
                for i in range(random.randint(4,8)):
                    sess = Sess(course_code=course.code,
                                date=today-timedelta(days=random.randint(1,60)),
                                duree=random.choice([1.5,2.0,2.5,3.0]),
                                theme=f"Chapitre {i+1}")
                    db.add(sess); db.flush()
                    for st in students:
                        if random.random()<0.12:
                            db.add(Attendance(id_session=sess.id,id_student=st.id))
            for st in students:
                for c in courses:
                    if random.random()>0.15:
                        db.add(Grade(id_student=st.id,course_code=c.code,
                                     note=round(random.uniform(8,20),2),
                                     coefficient=random.choice([1.0,1.5,2.0])))
            db.add(Notification(type="warning",titre="Absentéisme élevé",
                message="3 étudiants ont dépassé 20% d absences en MATH101."))
            db.add(Notification(type="info",titre="Session planifiée",
                message="INFO202 - Session prévue demain."))
            db.add(Notification(type="success",titre="Moyennes calculées",
                message="Les moyennes du semestre ont été mises à jour."))
            db.commit()
    except Exception as e:
        db.rollback(); print(f"Seed error: {e}")
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
                ("admin",     "admin123",     "admin",     None),
                ("enseignant","teach123",     "teacher",   None),
                ("secretaire","secr123",      "secretary", None),
                ("etudiant",  "etu123",       "student",   None),
                ("parent",    "parent123",    "parent",    None),
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
