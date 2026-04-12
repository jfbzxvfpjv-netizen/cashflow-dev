from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.database import get_db
from app.core.deps import get_current_user, require_role
from app.schemas.catalogs import EmployeeCreate, EmployeeUpdate, EmployeeSalaryUpdate, EmployeeResponse, SalaryHistoryResponse, PaginatedResponse
from app.services.catalog_service import EmployeeService

router = APIRouter(prefix="/employees", tags=["Catálogos — Empleados"])

def _filter_salary(emp, user):
    r = EmployeeResponse.model_validate(emp)
    if user.role not in ("admin", "contable"):
        r.salary_gross = None; r.salary_transfer = None; r.salary_effective_date = None
    return r

@router.get("", response_model=PaginatedResponse)
def list_employees(delegacion: Optional[str] = None, active_only: bool = True, search: Optional[str] = None, page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200), db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    d = current_user.delegacion if current_user.role == "gestor" else delegacion
    items, total = EmployeeService.list_employees(db, delegacion=d, active_only=active_only, search=search, page=page, page_size=page_size)
    return {"items": [_filter_salary(e, current_user) for e in items], "total": total, "page": page, "page_size": page_size, "pages": (total + page_size - 1) // page_size}

@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(employee_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return _filter_salary(EmployeeService.get_employee(db, employee_id), current_user)

@router.post("", response_model=EmployeeResponse, status_code=201)
def create_employee(data: EmployeeCreate, db: Session = Depends(get_db), current_user=Depends(require_role("admin"))):
    return EmployeeResponse.model_validate(EmployeeService.create_employee(db, data, current_user.id))

@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(employee_id: int, data: EmployeeUpdate, db: Session = Depends(get_db), current_user=Depends(require_role("admin"))):
    return EmployeeResponse.model_validate(EmployeeService.update_employee(db, employee_id, data, current_user.id))

@router.put("/{employee_id}/salary", response_model=EmployeeResponse)
def update_salary(employee_id: int, data: EmployeeSalaryUpdate, db: Session = Depends(get_db), current_user=Depends(require_role("admin", "contable"))):
    return EmployeeResponse.model_validate(EmployeeService.update_salary(db, employee_id, data, current_user.id))

@router.get("/{employee_id}/salary-history", response_model=List[SalaryHistoryResponse])
def get_salary_history(employee_id: int, db: Session = Depends(get_db), current_user=Depends(require_role("admin", "contable"))):
    return [SalaryHistoryResponse.model_validate(h) for h in EmployeeService.get_salary_history(db, employee_id)]
