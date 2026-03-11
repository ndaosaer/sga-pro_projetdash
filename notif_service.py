"""
Nafa Scolaire — Service de notifications push
Crée et stocke les notifications ciblées (parent, secrétaire, admin)
Utilisé par : presences, notes, paiements, alertes
"""
from datetime import datetime
from database import SessionLocal
from models import Notification, Student, User


def _notif_existe(db, titre, student_id, categorie):
    """Évite les doublons dans la même journée."""
    from datetime import date
    today = date.today()
    return db.query(Notification).filter(
        Notification.titre       == titre,
        Notification.student_id  == student_id,
        Notification.categorie   == categorie,
        Notification.created_at  >= datetime(today.year, today.month, today.day),
    ).first()


def push_absence(student_id: int, course_code: str, nb_abs: int,
                 nb_sess: int, taux: float):
    """Notifie parent + secrétaire quand un étudiant dépasse le seuil d'absence."""
    db = SessionLocal()
    try:
        stu = db.get(Student, student_id)
        if not stu:
            return

        niveau = "danger" if taux > 30 else "warning"
        titre  = f"Absence — {stu.nom} {stu.prenom} ({course_code})"
        msg    = (f"{stu.prenom} {stu.nom} a atteint {taux:.0f}% d'absences "
                  f"({nb_abs}/{nb_sess} séances) en {course_code}.")

        for dest in ("parent", "secretary", "admin"):
            if not _notif_existe(db, titre, student_id, "absence"):
                db.add(Notification(
                    type=niveau, titre=titre, message=msg,
                    lu=False, created_at=datetime.now(),
                    student_id=student_id, destinataire=dest,
                    categorie="absence",
                ))
        db.commit()
    finally:
        db.close()


def push_note_faible(student_id: int, course_code: str, note: float):
    """Notifie parent + secrétaire quand une note est en dessous du seuil."""
    db = SessionLocal()
    try:
        stu = db.get(Student, student_id)
        if not stu:
            return

        niveau = "danger" if note < 8 else "warning"
        titre  = f"Note faible — {stu.nom} {stu.prenom} ({course_code})"
        msg    = (f"{stu.prenom} {stu.nom} a obtenu {note:.2f}/20 en {course_code}. "
                  f"En dessous du seuil minimum de 10/20.")

        for dest in ("parent", "secretary"):
            if not _notif_existe(db, titre, student_id, "note"):
                db.add(Notification(
                    type=niveau, titre=titre, message=msg,
                    lu=False, created_at=datetime.now(),
                    student_id=student_id, destinataire=dest,
                    categorie="note",
                ))
        db.commit()
    finally:
        db.close()


def push_paiement(student_id: int, montant: float, statut: str):
    """Notifie le secrétariat et l'admin d'un paiement reçu."""
    db = SessionLocal()
    try:
        stu = db.get(Student, student_id)
        if not stu:
            return

        titre = f"Paiement — {stu.nom} {stu.prenom}"
        msg   = f"Paiement de {montant:,.0f} FCFA reçu. Statut : {statut}."

        for dest in ("secretary", "admin"):
            if not _notif_existe(db, titre, student_id, "paiement"):
                db.add(Notification(
                    type="success", titre=titre, message=msg,
                    lu=False, created_at=datetime.now(),
                    student_id=student_id, destinataire=dest,
                    categorie="paiement",
                ))
        db.commit()
    finally:
        db.close()


def push_info(titre: str, message: str, destinataire: str = "all"):
    """Notification générique d'information."""
    db = SessionLocal()
    try:
        db.add(Notification(
            type="info", titre=titre, message=message,
            lu=False, created_at=datetime.now(),
            student_id=None, destinataire=destinataire,
            categorie="info",
        ))
        db.commit()
    finally:
        db.close()


def get_notifs(destinataire: str, student_id: int = None,
               non_lues_seulement: bool = False, limit: int = 30):
    """Récupère les notifications pour un destinataire donné."""
    db = SessionLocal()
    try:
        q = db.query(Notification).filter(
            (Notification.destinataire == destinataire) |
            (Notification.destinataire == "all")
        )
        if student_id:
            q = q.filter(
                (Notification.student_id == student_id) |
                (Notification.student_id == None)
            )
        if non_lues_seulement:
            q = q.filter(Notification.lu == False)
        notifs = q.order_by(Notification.created_at.desc()).limit(limit).all()
        result = [{
            "id":          n.id,
            "type":        n.type,
            "titre":       n.titre,
            "message":     n.message,
            "lu":          n.lu,
            "created_at":  n.created_at.strftime("%d/%m/%Y %H:%M") if n.created_at else "",
            "categorie":   n.categorie or "info",
            "student_id":  n.student_id,
        } for n in notifs]
        return result
    finally:
        db.close()


def marquer_lues(notif_ids: list):
    db = SessionLocal()
    try:
        db.query(Notification).filter(
            Notification.id.in_(notif_ids)
        ).update({"lu": True}, synchronize_session=False)
        db.commit()
    finally:
        db.close()


def count_non_lues(destinataire: str, student_id: int = None) -> int:
    db = SessionLocal()
    try:
        q = db.query(Notification).filter(
            Notification.lu == False,
            (Notification.destinataire == destinataire) |
            (Notification.destinataire == "all")
        )
        if student_id:
            q = q.filter(
                (Notification.student_id == student_id) |
                (Notification.student_id == None)
            )
        return q.count()
    finally:
        db.close()
