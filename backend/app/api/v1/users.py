"""
Router de gestión de usuarios — /api/v1/users
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user, require_role
from app.models.user import User
from app.schemas.user import (UserCreate, UserUpdate, UserResponse,
    UserListResponse, PasswordChange, PasswordChangeSelf)
from app.services.user_service import (UserServiceError, list_users, get_user_by_id,
    create_user, update_user, change_password_admin, change_password_self)

router = APIRouter(prefix="/users", tags=["Usuarios"])


@router.get("", response_model=UserListResponse)
async def get_users(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    role: str | None = None, delegacion: str | None = None,
    active: bool | None = None,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    result = list_users(db, page=page, page_size=page_size, role=role,
                        delegacion=delegacion, active=active)
    return UserListResponse(
        items=[UserResponse.model_validate(u) for u in result["items"]],
        total=result["total"], page=result["page"], page_size=result["page_size"],
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, current_user: User = Depends(require_role("admin")),
                   db: Session = Depends(get_db)):
    user = get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    return UserResponse.model_validate(user)


@router.post("", response_model=UserResponse, status_code=201)
async def create_new_user(body: UserCreate, current_user: User = Depends(require_role("admin")),
                          db: Session = Depends(get_db)):
    try:
        user = create_user(db, username=body.username, password=body.password,
            full_name=body.full_name, role=body.role, delegacion=body.delegacion,
            created_by=current_user)
        return UserResponse.model_validate(user)
    except UserServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.put("/{user_id}", response_model=UserResponse)
async def update_existing_user(user_id: int, body: UserUpdate,
    current_user: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    try:
        user = update_user(db, user_id=user_id,
            update_data=body.model_dump(exclude_none=True), updated_by=current_user)
        return UserResponse.model_validate(user)
    except UserServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.put("/{user_id}/password", status_code=204)
async def admin_change_password(user_id: int, body: PasswordChange,
    current_user: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    try:
        change_password_admin(db, user_id, body.new_password, changed_by=current_user)
    except UserServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.put("/me/password", status_code=204)
async def self_change_password(body: PasswordChangeSelf,
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        change_password_self(db, current_user, body.current_password, body.new_password)
    except UserServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
