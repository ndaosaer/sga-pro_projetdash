from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, UniqueConstraint, Boolean, Text
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id            = Column(Integer, primary_key=True, autoincrement=True)
    username      = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    # Rôles : admin | teacher | student | parent | secretary
    role          = Column(String(50), default="teacher")
    # Pour student -> id de Student, pour parent -> id de Student (son enfant)
    linked_id     = Column(Integer, nullable=True)
    created_at    = Column(DateTime)

class Student(Base):
    __tablename__ = "students"
    id             = Column(Integer, primary_key=True, autoincrement=True)
    nom            = Column(String(100), nullable=False)
    prenom         = Column(String(100), nullable=False)
    email          = Column(String(200), unique=True, nullable=False)
    date_naissance = Column(Date, nullable=True)
    classe_id      = Column(Integer, ForeignKey('classes.id', ondelete='SET NULL'), nullable=True)
    classe         = relationship('Classe', back_populates='etudiants', lazy='select')
    actif          = Column(Boolean, default=True)
    created_at     = Column(DateTime)
    attendances    = relationship("Attendance", back_populates="student", cascade="all, delete-orphan", lazy="select")
    grades         = relationship("Grade", back_populates="student", cascade="all, delete-orphan", lazy="select")

class Course(Base):
    __tablename__ = "courses"
    code           = Column(String(20), primary_key=True)
    libelle        = Column(String(200), nullable=False)
    volume_horaire = Column(Float, nullable=False)
    enseignant     = Column(String(200), nullable=True)
    # Username de l'enseignant propriétaire
    teacher_username = Column(String(100), nullable=True)
    description    = Column(Text, nullable=True)
    couleur        = Column(String(7), default="#B8922A")
    created_at     = Column(DateTime)
    sessions       = relationship("Session", back_populates="course", cascade="all, delete-orphan", lazy="select")
    grades         = relationship("Grade", back_populates="course", cascade="all, delete-orphan", lazy="select")

class Session(Base):
    __tablename__ = "sessions"
    id          = Column(Integer, primary_key=True, autoincrement=True)
    course_code = Column(String(20), ForeignKey("courses.code", ondelete="CASCADE"), nullable=False)
    date        = Column(Date, nullable=False)
    duree       = Column(Float, nullable=False)
    theme       = Column(String(500), nullable=True)
    objectifs   = Column(Text, nullable=True)
    created_at  = Column(DateTime)
    course      = relationship("Course", back_populates="sessions", lazy="select")
    attendances = relationship("Attendance", back_populates="session", cascade="all, delete-orphan", lazy="select")

class Attendance(Base):
    __tablename__ = "attendance"
    id_session = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), primary_key=True)
    id_student = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), primary_key=True)
    justifiee  = Column(Boolean, default=False)
    __table_args__ = (UniqueConstraint("id_session", "id_student", name="uq_attendance"),)
    session = relationship("Session", back_populates="attendances", lazy="select")
    student = relationship("Student", back_populates="attendances", lazy="select")

class Grade(Base):
    __tablename__ = "grades"
    id          = Column(Integer, primary_key=True, autoincrement=True)
    id_student  = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    course_code = Column(String(20), ForeignKey("courses.code", ondelete="CASCADE"), nullable=False)
    note        = Column(Float, nullable=False)
    coefficient = Column(Float, nullable=False, default=1.0)
    commentaire = Column(Text, nullable=True)
    created_at  = Column(DateTime)
    __table_args__ = (UniqueConstraint("id_student", "course_code", name="uq_grade_student_course"),)
    student = relationship("Student", back_populates="grades", lazy="select")
    course  = relationship("Course", back_populates="grades", lazy="select")

class Notification(Base):
    __tablename__ = "notifications"
    id           = Column(Integer, primary_key=True, autoincrement=True)
    type         = Column(String(50), nullable=False)   # danger / warning / info / success
    titre        = Column(String(200), nullable=False)
    message      = Column(Text, nullable=False)
    lu           = Column(Boolean, default=False)
    created_at   = Column(DateTime)
    # Destinataires ciblés
    student_id   = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=True)
    destinataire = Column(String(50), nullable=True)   # "parent", "secretary", "admin", "all"
    categorie    = Column(String(50), nullable=True)   # "absence", "note", "paiement", "info"
    student      = relationship("Student", lazy="select", foreign_keys=[student_id])


# ═══════════════════════════════════════════════
# MODULE CONCOURS
# ═══════════════════════════════════════════════

class Concours(Base):
    __tablename__ = "concours"
    id            = Column(Integer, primary_key=True, autoincrement=True)
    nom           = Column(String(200), nullable=False)
    annee         = Column(Integer, nullable=False)
    description   = Column(Text, nullable=True)
    date_ouverture = Column(Date, nullable=True)   # ouverture des inscriptions
    date_cloture  = Column(Date, nullable=True)    # cloture des inscriptions
    date_epreuve  = Column(Date, nullable=True)    # date du concours
    date_resultats = Column(Date, nullable=True)   # publication des resultats
    frais_dossier = Column(Float, default=0.0)     # frais en FCFA
    actif         = Column(Boolean, default=True)
    created_at    = Column(DateTime)
    candidats     = relationship("Candidat", back_populates="concours", cascade="all, delete-orphan", lazy="select")
    communiques   = relationship("Communique", back_populates="concours", cascade="all, delete-orphan", lazy="select")


class Candidat(Base):
    __tablename__ = "candidats"
    id              = Column(Integer, primary_key=True, autoincrement=True)
    concours_id     = Column(Integer, ForeignKey("concours.id", ondelete="CASCADE"), nullable=False)
    # Identite
    nom             = Column(String(100), nullable=False)
    prenom          = Column(String(100), nullable=False)
    email           = Column(String(200), nullable=False)
    telephone       = Column(String(30), nullable=True)
    date_naissance  = Column(Date, nullable=True)
    nationalite     = Column(String(100), nullable=True)
    # Cursus
    niveau_etudes   = Column(String(100), nullable=True)   # Bac+2, Licence...
    etablissement   = Column(String(200), nullable=True)
    filiere         = Column(String(200), nullable=True)
    # Dossier
    statut          = Column(String(30), default="en_attente")
    # en_attente | dossier_incomplet | dossier_complet | valide | rejete | admis
    pieces_jointes  = Column(Text, nullable=True)  # JSON liste des fichiers
    note_admin      = Column(Text, nullable=True)  # commentaire de l'admin
    # Paiement
    paiement_statut = Column(String(20), default="non_paye")  # non_paye | paye | simule
    paiement_ref    = Column(String(100), nullable=True)
    paiement_date   = Column(DateTime, nullable=True)
    paiement_mode   = Column(String(50), nullable=True)  # wave | orange | carte | simulation
    # Admission
    admis           = Column(Boolean, default=False)
    student_id      = Column(Integer, ForeignKey("students.id"), nullable=True)  # apres conversion
    numero_candidat = Column(String(50), nullable=True)  # numero attribue
    created_at      = Column(DateTime)
    concours        = relationship("Concours", back_populates="candidats", lazy="select")
    student         = relationship("Student", lazy="select")


class Communique(Base):
    __tablename__ = "communiques"
    id          = Column(Integer, primary_key=True, autoincrement=True)
    concours_id = Column(Integer, ForeignKey("concours.id", ondelete="CASCADE"), nullable=False)
    titre       = Column(String(300), nullable=False)
    contenu     = Column(Text, nullable=False)
    type_comm   = Column(String(50), default="info")  # info | urgent | resultat
    publie      = Column(Boolean, default=True)
    created_at  = Column(DateTime)
    concours    = relationship("Concours", back_populates="communiques", lazy="select")


# ═══════════════════════════════════════════════
# MODULE PAIEMENTS SCOLARITE
# ═══════════════════════════════════════════════

class FraisScolarite(Base):
    """Montant total du par un etudiant pour une annee academique."""
    __tablename__ = "frais_scolarite"
    id            = Column(Integer, primary_key=True, autoincrement=True)
    student_id    = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    annee         = Column(String(9), nullable=False)   # ex: 2025-2026
    montant_total = Column(Float, nullable=False)
    echeances     = Column(Integer, default=1)          # nb de tranches
    note          = Column(Text, nullable=True)
    created_at    = Column(DateTime)
    student       = relationship("Student", lazy="select")
    paiements     = relationship("Paiement", back_populates="frais",
                                 cascade="all, delete-orphan", lazy="select")


class Paiement(Base):
    """Un versement effectue par un etudiant."""
    __tablename__ = "paiements"
    id            = Column(Integer, primary_key=True, autoincrement=True)
    frais_id      = Column(Integer, ForeignKey("frais_scolarite.id", ondelete="CASCADE"), nullable=False)
    student_id    = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    montant       = Column(Float, nullable=False)
    date_paiement = Column(Date, nullable=False)
    mode          = Column(String(50), nullable=False)  # especes | wave | orange | virement | carte
    reference     = Column(String(100), nullable=True)
    tranche       = Column(Integer, default=1)          # numero de la tranche
    valide        = Column(Boolean, default=True)
    note          = Column(Text, nullable=True)
    created_at    = Column(DateTime)
    frais         = relationship("FraisScolarite", back_populates="paiements", lazy="select")
    student       = relationship("Student", lazy="select")


# ═══════════════════════════════════════════════
# MODULE MESSAGERIE
# ═══════════════════════════════════════════════

class Conversation(Base):
    """Fil de discussion entre participants."""
    __tablename__ = "conversations"
    id          = Column(Integer, primary_key=True, autoincrement=True)
    sujet       = Column(String(300), nullable=False)
    type_conv   = Column(String(20), default="prive")   # prive | groupe
    created_by  = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at  = Column(DateTime)
    messages    = relationship("Message", back_populates="conversation",
                               cascade="all, delete-orphan", lazy="select",
                               order_by="Message.created_at")
    participants = relationship("ConvParticipant", back_populates="conversation",
                                cascade="all, delete-orphan", lazy="select")


class ConvParticipant(Base):
    """Lie un utilisateur a une conversation."""
    __tablename__ = "conv_participants"
    id              = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"))
    user_id         = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    lu_at           = Column(DateTime, nullable=True)   # derniere lecture
    conversation    = relationship("Conversation", back_populates="participants", lazy="select")
    user            = relationship("User", lazy="select")


class Message(Base):
    """Un message dans une conversation."""
    __tablename__ = "messages"
    id              = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"))
    sender_id       = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    contenu         = Column(Text, nullable=False)
    piece_jointe    = Column(String(500), nullable=True)  # chemin fichier
    pj_nom          = Column(String(200), nullable=True)  # nom original
    pj_type         = Column(String(50),  nullable=True)  # pdf | image
    created_at      = Column(DateTime)
    conversation    = relationship("Conversation", back_populates="messages", lazy="select")
    sender          = relationship("User", lazy="select")


# ═══════════════════════════════════════════════
# MODULE EMPLOI DU TEMPS
# ═══════════════════════════════════════════════

class Creneau(Base):
    """Un creneau dans l'emploi du temps hebdomadaire."""
    __tablename__ = "creneaux"
    id           = Column(Integer, primary_key=True, autoincrement=True)
    course_code  = Column(String(50), ForeignKey("courses.code", ondelete="CASCADE"), nullable=False)
    jour         = Column(Integer, nullable=False)   # 0=Lundi ... 4=Vendredi
    heure_debut  = Column(Float, nullable=False)     # ex: 8.0 = 08h00, 8.5 = 08h30
    heure_fin    = Column(Float, nullable=False)     # ex: 10.0 = 10h00
    salle        = Column(String(100), nullable=True)
    enseignant   = Column(String(200), nullable=True)
    couleur      = Column(String(7),   nullable=True)
    created_at   = Column(DateTime)
    classe_id    = Column(Integer, ForeignKey('classes.id', ondelete='SET NULL'), nullable=True)
    course       = relationship("Course", lazy="select")
    classe       = relationship("Classe", back_populates="creneaux", lazy="select")


# ═══════════════════════════════════════════════
# MODULE CLASSES / NIVEAUX
# ═══════════════════════════════════════════════

class Niveau(Base):
    """Niveau academique : Licence, Master, Doctorat."""
    __tablename__ = "niveaux"
    id       = Column(Integer, primary_key=True, autoincrement=True)
    nom      = Column(String(100), nullable=False)   # ex: Licence, Master
    abrev    = Column(String(20),  nullable=False)   # ex: L, M, D
    ordre    = Column(Integer, default=1)            # pour tri
    classes  = relationship("Classe", back_populates="niveau",
                            cascade="all, delete-orphan", lazy="select")


class Classe(Base):
    """Une classe = un niveau + une filiere + une annee. ex: L3 Statistique."""
    __tablename__ = "classes"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    nom        = Column(String(150), nullable=False)    # ex: L3 Statistique
    code       = Column(String(30),  nullable=False, unique=True)  # ex: L3-STAT
    niveau_id  = Column(Integer, ForeignKey("niveaux.id"), nullable=False)
    filiere    = Column(String(100), nullable=True)     # ex: Statistique, Economie
    annee      = Column(String(9),   nullable=True)     # ex: 2025-2026
    effectif_max = Column(Integer,   default=40)
    actif      = Column(Boolean,     default=True)
    couleur    = Column(String(7),   nullable=True)     # couleur UI
    created_at = Column(DateTime)
    niveau     = relationship("Niveau", back_populates="classes", lazy="select")
    etudiants  = relationship("Student", back_populates="classe", lazy="select")
    cours_classes = relationship("CoursClasse", back_populates="classe",
                                 cascade="all, delete-orphan", lazy="select")
    creneaux   = relationship("Creneau", back_populates="classe", lazy="select")


class CoursClasse(Base):
    """Lien entre un cours et une classe (avec enseignant specifique si besoin)."""
    __tablename__ = "cours_classes"
    id          = Column(Integer, primary_key=True, autoincrement=True)
    course_code = Column(String(50), ForeignKey("courses.code", ondelete="CASCADE"))
    classe_id   = Column(Integer,   ForeignKey("classes.id",   ondelete="CASCADE"))
    enseignant  = Column(String(200), nullable=True)  # surcharge si different du cours
    created_at  = Column(DateTime)
    course      = relationship("Course", lazy="select")
    classe      = relationship("Classe", back_populates="cours_classes", lazy="select")
