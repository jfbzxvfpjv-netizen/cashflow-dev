"""
Servicio de gestión de usuarios — CRUD y cambio de contraseña.
"""

from sqlalchemy.orm import Session
from app.models.user import User
from app.models.audit_log import AuditLog
from app.core.security import hash_password, verify_password, validate_password_policy


class UserServiceError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


def list_users(db: Session, page: int = 1, page_size: int = 20,
               role: str | None = None, delegacion: str | None = None,
               active: bool | None = None) -> dict:
    query = db.query(User)
    if role is not None:
        query = query.filter(User.role == role)
    if delegacion is not None:
        query = query.filter(User.delegacion == delegacion)
    if active is not None:
        query = query.filter(User.active == active)

    total = query.count()
    items = query.order_by(User.id).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def create_user(db: Session, username: str, password: str, full_name: str,
                role: str, delegacion: str, created_by: User) -> User:
    if get_user_by_username(db, username):
        raise UserServiceError(f"El nombre de usuario '{username}' ya está en uso.", 409)

    errors = validate_password_policy(password)
    if errors:
        raise UserServiceError("La contraseña no cumple la política: " + " ".join(errors))

    if role == "gestor" and delegacion == "Ambas":
        raise UserServiceError("El Gestor de Caja debe asignarse a Bata o Malabo, no a 'Ambas'.")

    user = User(username=username, password_hash=hash_password(password),
                full_name=full_name, role=role, delegacion=delegacion, active=True)
    db.add(user)
    db.flush()

    db.add(AuditLog(user_id=created_by.id, action="CREATE_USER", entity="users",
                    entity_id=user.id, details={"username": username, "role": role, "delegacion": delegacion}))
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user_id: int, update_data: dict, updated_by: User) -> User:
    user = get_user_by_id(db, user_id)
    if user is None:
        raise UserServiceError("Usuario no encontrado.", 404)

    old_values, new_values = {}, {}
    for field, value in update_data.items():
        if value is not None and hasattr(user, field):
            old_values[field] = getattr(user, field)
            setattr(user, field, value)
            new_values[field] = value

    if user.role == "gestor" and user.delegacion == "Ambas":
        raise UserServiceError("El Gestor de Caja debe asignarse a Bata o Malabo.")

    if not new_values:
        raise UserServiceError("No se proporcionaron campos para actualizar.")

    db.add(AuditLog(user_id=updated_by.id, action="UPDATE_USER", entity="users",
                    entity_id=user.id, details={"old": old_values, "new": new_values}))
    db.commit()
    db.refresh(user)
    return user


def change_password_admin(db: Session, user_id: int, new_password: str, changed_by: User) -> None:
    user = get_user_by_id(db, user_id)
    if user is None:
        raise UserServiceError("Usuario no encontrado.", 404)

    errors = validate_password_policy(new_password)
    if errors:
        raise UserServiceError("La contraseña no cumple la política: " + " ".join(errors))

    user.password_hash = hash_password(new_password)
    db.add(AuditLog(user_id=changed_by.id, action="CHANGE_PASSWORD_ADMIN", entity="users",
                    entity_id=user.id, details={"target_username": user.username}))
    db.commit()


def change_password_self(db: Session, user: User, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user.password_hash):
        raise UserServiceError("La contraseña actual no es correcta.", 401)

    errors = validate_password_policy(new_password)
    if errors:
        raise UserServiceError("La nueva contraseña no cumple la política: " + " ".join(errors))

    user.password_hash = hash_password(new_password)
    db.add(AuditLog(user_id=user.id, action="CHANGE_PASSWORD_SELF", entity="users",
                    entity_id=user.id, details={"username": user.username}))
    db.commit()
