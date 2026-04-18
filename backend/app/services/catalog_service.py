"""
Módulo 4 — Servicio de catálogos (versión síncrona).
Lógica de negocio CRUD para todos los catálogos.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from fastapi import HTTPException
from typing import Optional, List, Tuple

from app.models.cash_flow import Transaction
from app.models import (
    Project, Work, TransactionCategory, TransactionSubcategory,
    Supplier, Employee, Partner, CorporateAccount, Vehicle,
    EmployeeSalaryHistory, AuditLog,
)


def _paginate(query, page: int, page_size: int):
    return query.offset((page - 1) * page_size).limit(page_size)


def _log_audit(db, user_id, delegacion, action, entity, entity_id, details=None):
    db.add(AuditLog(user_id=user_id, delegacion=delegacion, action=action,
                    entity=entity, entity_id=entity_id, details=details))


# ── PROYECTOS ──────────────────────────────────────────────────

class ProjectService:
    @staticmethod
    def list_projects(db: Session, active_only=True, search=None, page=1, page_size=50):
        query = db.query(Project)
        if active_only:
            query = query.filter(Project.active == True)
        if search:
            p = f"%{search}%"
            query = query.filter(or_(Project.code.ilike(p), Project.name.ilike(p)))
        total = query.count()
        items = _paginate(query.order_by(Project.code), page, page_size).all()
        return items, total

    @staticmethod
    def get_project(db: Session, project_id: int):
        p = db.query(Project).get(project_id)
        if not p:
            raise HTTPException(404, "Proyecto no encontrado")
        return p

    @staticmethod
    def create_project(db: Session, data, user_id: int):
        if db.query(Project).filter(Project.code == data.code).first():
            raise HTTPException(409, f"Ya existe un proyecto con código '{data.code}'")
        project = Project(**data.model_dump())
        db.add(project)
        db.flush()
        _log_audit(db, user_id, None, "CREATE_PROJECT", "projects", project.id)
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def update_project(db: Session, project_id: int, data, user_id: int):
        project = ProjectService.get_project(db, project_id)
        update_data = data.model_dump(exclude_unset=True)
        if "code" in update_data and update_data["code"] != project.code:
            if db.query(Project).filter(Project.code == update_data["code"], Project.id != project_id).first():
                raise HTTPException(409, f"Ya existe un proyecto con código '{update_data['code']}'")
        for k, v in update_data.items():
            setattr(project, k, v)
        _log_audit(db, user_id, None, "UPDATE_PROJECT", "projects", project_id)
        db.commit()
        db.refresh(project)
        return project


# ── OBRAS ──────────────────────────────────────────────────────

class WorkService:
    @staticmethod
    def list_works(db: Session, project_id=None, active_only=True, search=None, page=1, page_size=100):
        query = db.query(Work)
        if project_id:
            query = query.filter(Work.project_id == project_id)
        if active_only:
            query = query.filter(Work.active == True)
        if search:
            p = f"%{search}%"
            query = query.filter(or_(Work.code.ilike(p), Work.name.ilike(p)))
        total = query.count()
        items = _paginate(query.order_by(Work.project_id, Work.code), page, page_size).all()
        return items, total

    @staticmethod
    def get_work(db: Session, work_id: int):
        w = db.query(Work).get(work_id)
        if not w:
            raise HTTPException(404, "Obra no encontrada")
        return w

    @staticmethod
    def create_work(db: Session, data, user_id: int):
        project = db.query(Project).get(data.project_id)
        if not project:
            raise HTTPException(404, "Proyecto no encontrado")
        if db.query(Work).filter(Work.project_id == data.project_id, Work.code == data.code).first():
            raise HTTPException(409, f"Ya existe obra '{data.code}' en proyecto '{project.code}'")
        work = Work(**data.model_dump())
        db.add(work)
        db.flush()
        _log_audit(db, user_id, None, "CREATE_WORK", "works", work.id)
        db.commit()
        db.refresh(work)
        return work

    @staticmethod
    def create_work_inline(db: Session, project_id, code, name, user_id):
        existing = db.query(Work).filter(Work.project_id == project_id, Work.code == code).first()
        if existing:
            return existing
        project = db.query(Project).get(project_id)
        if not project:
            raise HTTPException(404, "Proyecto no encontrado")
        work = Work(project_id=project_id, code=code, name=name)
        db.add(work)
        db.flush()
        _log_audit(db, user_id, None, "CREATE_WORK_INLINE", "works", work.id)
        db.commit()
        db.refresh(work)
        return work

    @staticmethod
    def update_work(db: Session, work_id: int, data, user_id: int):
        work = WorkService.get_work(db, work_id)
        update_data = data.model_dump(exclude_unset=True)
        for k, v in update_data.items():
            setattr(work, k, v)
        _log_audit(db, user_id, None, "UPDATE_WORK", "works", work_id)
        db.commit()
        db.refresh(work)
        return work


# ── CATEGORÍAS ─────────────────────────────────────────────────

class CategoryService:
    @staticmethod
    def list_categories(db: Session, type_filter=None, active_only=True, page=1, page_size=50):
        query = db.query(TransactionCategory)
        if active_only:
            query = query.filter(TransactionCategory.active == True)
        if type_filter and type_filter in ("income", "expense"):
            query = query.filter(or_(TransactionCategory.type == type_filter, TransactionCategory.type == "both"))
        elif type_filter:
            query = query.filter(TransactionCategory.type == type_filter)
        total = query.count()
        items = _paginate(query.order_by(TransactionCategory.name), page, page_size).all()
        return items, total

    @staticmethod
    def get_category(db: Session, category_id: int):
        c = db.query(TransactionCategory).get(category_id)
        if not c:
            raise HTTPException(404, "Categoría no encontrada")
        return c

    @staticmethod
    def create_category(db: Session, data, user_id: int):
        if db.query(TransactionCategory).filter(TransactionCategory.name == data.name).first():
            raise HTTPException(409, f"Ya existe categoría '{data.name}'")
        cat = TransactionCategory(**data.model_dump())
        db.add(cat)
        db.flush()
        _log_audit(db, user_id, None, "CREATE_CATEGORY", "transaction_categories", cat.id)
        db.commit()
        db.refresh(cat)
        return cat

    @staticmethod
    def update_category(db: Session, category_id: int, data, user_id: int):
        cat = CategoryService.get_category(db, category_id)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(cat, k, v)
        _log_audit(db, user_id, None, "UPDATE_CATEGORY", "transaction_categories", category_id)
        db.commit()
        db.refresh(cat)
        return cat


# ── SUBCATEGORÍAS ──────────────────────────────────────────────

class SubcategoryService:
    @staticmethod
    def list_subcategories(db: Session, category_id: int, active_only=True):
        query = db.query(TransactionSubcategory).filter(TransactionSubcategory.category_id == category_id)
        if active_only:
            query = query.filter(TransactionSubcategory.active == True)
        return query.order_by(TransactionSubcategory.name).all()

    @staticmethod
    def get_subcategory(db: Session, subcategory_id: int):
        s = db.query(TransactionSubcategory).get(subcategory_id)
        if not s:
            raise HTTPException(404, "Subcategoría no encontrada")
        return s

    @staticmethod
    def create_subcategory(db: Session, data, user_id: int):
        cat = db.query(TransactionCategory).get(data.category_id)
        if not cat:
            raise HTTPException(404, "Categoría no encontrada")
        if db.query(TransactionSubcategory).filter(
            TransactionSubcategory.category_id == data.category_id,
            TransactionSubcategory.name == data.name
        ).first():
            raise HTTPException(409, f"Ya existe subcategoría '{data.name}' en '{cat.name}'")
        sub = TransactionSubcategory(**data.model_dump())
        db.add(sub)
        db.flush()
        _log_audit(db, user_id, None, "CREATE_SUBCATEGORY", "transaction_subcategories", sub.id)
        db.commit()
        db.refresh(sub)
        return sub

    @staticmethod
    def update_subcategory(db: Session, subcategory_id: int, data, user_id: int):
        sub = SubcategoryService.get_subcategory(db, subcategory_id)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(sub, k, v)
        _log_audit(db, user_id, None, "UPDATE_SUBCATEGORY", "transaction_subcategories", subcategory_id)
        db.commit()
        db.refresh(sub)
        return sub


# ── PROVEEDORES ────────────────────────────────────────────────

class SupplierService:
    @staticmethod
    def list_suppliers(db: Session, supplier_type=None, active_only=True, search=None, page=1, page_size=50):
        query = db.query(Supplier)
        if active_only:
            query = query.filter(Supplier.active == True)
        if supplier_type:
            query = query.filter(Supplier.supplier_type == supplier_type)
        if search:
            p = f"%{search}%"
            query = query.filter(or_(Supplier.code.ilike(p), Supplier.name.ilike(p)))
        total = query.count()
        items = _paginate(query.order_by(Supplier.name), page, page_size).all()
        return items, total

    @staticmethod
    def get_supplier(db: Session, supplier_id: int):
        s = db.query(Supplier).get(supplier_id)
        if not s:
            raise HTTPException(404, "Proveedor no encontrado")
        return s

    @staticmethod
    def create_supplier(db: Session, data, user_id: int):
        if db.query(Supplier).filter(Supplier.code == data.code).first():
            raise HTTPException(409, f"Ya existe proveedor con código '{data.code}'")
        sup = Supplier(**data.model_dump())
        db.add(sup)
        db.flush()
        _log_audit(db, user_id, None, "CREATE_SUPPLIER", "suppliers", sup.id)
        db.commit()
        db.refresh(sup)
        return sup

    @staticmethod
    def update_supplier(db: Session, supplier_id: int, data, user_id: int):
        sup = SupplierService.get_supplier(db, supplier_id)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(sup, k, v)
        _log_audit(db, user_id, None, "UPDATE_SUPPLIER", "suppliers", supplier_id)
        db.commit()
        db.refresh(sup)
        return sup


# ── EMPLEADOS ──────────────────────────────────────────────────

class EmployeeService:
    @staticmethod
    def list_employees(db: Session, delegacion=None, active_only=True, search=None, page=1, page_size=50):
        query = db.query(Employee)
        if active_only:
            query = query.filter(Employee.active == True)
        if delegacion:
            query = query.filter(Employee.delegacion == delegacion)
        if search:
            p = f"%{search}%"
            query = query.filter(or_(Employee.code.ilike(p), Employee.full_name.ilike(p)))
        total = query.count()
        items = _paginate(query.order_by(Employee.full_name), page, page_size).all()
        return items, total

    @staticmethod
    def get_employee(db: Session, employee_id: int):
        e = db.query(Employee).get(employee_id)
        if not e:
            raise HTTPException(404, "Empleado no encontrado")
        return e

    @staticmethod
    def create_employee(db: Session, data, user_id: int):
        if db.query(Employee).filter(Employee.code == data.code).first():
            raise HTTPException(409, f"Ya existe empleado con código '{data.code}'")
        emp = Employee(**data.model_dump())
        db.add(emp)
        db.flush()
        db.add(EmployeeSalaryHistory(
            employee_id=emp.id, salary_gross=data.salary_gross,
            salary_transfer=data.salary_transfer,
            effective_date=data.salary_effective_date, created_by=user_id))
        _log_audit(db, user_id, data.delegacion, "CREATE_EMPLOYEE", "employees", emp.id)
        db.commit()
        db.refresh(emp)
        return emp

    @staticmethod
    def update_employee(db: Session, employee_id: int, data, user_id: int):
        emp = EmployeeService.get_employee(db, employee_id)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(emp, k, v)
        _log_audit(db, user_id, emp.delegacion, "UPDATE_EMPLOYEE", "employees", employee_id)
        db.commit()
        db.refresh(emp)
        return emp

    @staticmethod
    def update_salary(db: Session, employee_id: int, data, user_id: int):
        emp = EmployeeService.get_employee(db, employee_id)
        emp.salary_gross = data.salary_gross
        emp.salary_transfer = data.salary_transfer
        emp.salary_effective_date = data.salary_effective_date
        db.add(EmployeeSalaryHistory(
            employee_id=employee_id, salary_gross=data.salary_gross,
            salary_transfer=data.salary_transfer,
            effective_date=data.salary_effective_date, created_by=user_id))
        _log_audit(db, user_id, emp.delegacion, "UPDATE_SALARY", "employees", employee_id)
        db.commit()
        db.refresh(emp)
        return emp

    @staticmethod
    def get_salary_history(db: Session, employee_id: int):
        return db.query(EmployeeSalaryHistory).filter(
            EmployeeSalaryHistory.employee_id == employee_id
        ).order_by(EmployeeSalaryHistory.effective_date.desc()).all()


# ── SOCIOS ─────────────────────────────────────────────────────

class PartnerService:
    @staticmethod
    def list_partners(db: Session, active_only=True):
        query = db.query(Partner)
        if active_only:
            query = query.filter(Partner.active == True)
        return query.order_by(Partner.code).all()

    @staticmethod
    def get_partner(db: Session, partner_id: int):
        p = db.query(Partner).get(partner_id)
        if not p:
            raise HTTPException(404, "Socio no encontrado")
        return p

    @staticmethod
    def create_partner(db: Session, data, user_id: int):
        if db.query(Partner).filter(Partner.code == data.code).first():
            raise HTTPException(409, f"Ya existe socio con código '{data.code}'")
        partner = Partner(**data.model_dump())
        db.add(partner)
        db.flush()
        _log_audit(db, user_id, None, "CREATE_PARTNER", "partners", partner.id)
        db.commit()
        db.refresh(partner)
        return partner

    @staticmethod
    def update_partner(db: Session, partner_id: int, data, user_id: int):
        partner = PartnerService.get_partner(db, partner_id)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(partner, k, v)
        _log_audit(db, user_id, None, "UPDATE_PARTNER", "partners", partner_id)
        db.commit()
        db.refresh(partner)
        return partner


# ── CUENTAS CORPORATIVAS ──────────────────────────────────────

class CorporateAccountService:
    @staticmethod
    def list_accounts(db: Session, delegacion=None, active_only=True):
        query = db.query(CorporateAccount)
        if active_only:
            query = query.filter(CorporateAccount.active == True)
        if delegacion:
            query = query.filter(CorporateAccount.delegacion == delegacion)
        return query.order_by(CorporateAccount.bank_name).all()

    @staticmethod
    def get_account(db: Session, account_id: int):
        a = db.query(CorporateAccount).get(account_id)
        if not a:
            raise HTTPException(404, "Cuenta no encontrada")
        return a

    @staticmethod
    def create_account(db: Session, data, user_id: int):
        acc = CorporateAccount(**data.model_dump())
        db.add(acc)
        db.flush()
        _log_audit(db, user_id, data.delegacion, "CREATE_CORPORATE_ACCOUNT", "corporate_accounts", acc.id)
        db.commit()
        db.refresh(acc)
        return acc

    @staticmethod
    def update_account(db: Session, account_id: int, data, user_id: int):
        acc = CorporateAccountService.get_account(db, account_id)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(acc, k, v)
        _log_audit(db, user_id, acc.delegacion, "UPDATE_CORPORATE_ACCOUNT", "corporate_accounts", account_id)
        db.commit()
        db.refresh(acc)
        return acc


# ── VEHÍCULOS ──────────────────────────────────────────────────

class VehicleService:
    @staticmethod
    def list_vehicles(db: Session, delegacion=None, active_only=True, search=None, page=1, page_size=50):
        query = db.query(Vehicle)
        if active_only:
            query = query.filter(Vehicle.active == True)
        if delegacion:
            query = query.filter(Vehicle.delegacion == delegacion)
        if search:
            p = f"%{search}%"
            query = query.filter(or_(Vehicle.plate.ilike(p), Vehicle.brand.ilike(p)))
        total = query.count()
        items = _paginate(query.order_by(Vehicle.plate), page, page_size).all()
        return items, total

    @staticmethod
    def get_vehicle(db: Session, vehicle_id: int):
        v = db.query(Vehicle).get(vehicle_id)
        if not v:
            raise HTTPException(404, "Vehículo no encontrado")
        return v

    @staticmethod
    def create_vehicle(db: Session, data, user_id: int):
        if db.query(Vehicle).filter(Vehicle.plate == data.plate).first():
            raise HTTPException(409, f"Ya existe vehículo con matrícula '{data.plate}'")
        veh = Vehicle(**data.model_dump())
        db.add(veh)
        db.flush()
        _log_audit(db, user_id, data.delegacion, "CREATE_VEHICLE", "vehicles", veh.id)
        db.commit()
        db.refresh(veh)
        return veh

    @staticmethod
    def update_vehicle(db: Session, vehicle_id: int, data, user_id: int):
        veh = VehicleService.get_vehicle(db, vehicle_id)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(veh, k, v)
        _log_audit(db, user_id, veh.delegacion, "UPDATE_VEHICLE", "vehicles", vehicle_id)
        db.commit()
        db.refresh(veh)
        return veh


# ── BORRADO CONDICIONAL (añadido M4) ──────────────────────────

class CategoryDeleteService:
    @staticmethod
    def delete_category(db, category_id: int, user_id: int):
        """Elimina una categoría solo si no tiene subcategorías ni transacciones."""
        cat = db.query(TransactionCategory).get(category_id)
        if not cat:
            raise HTTPException(404, "Categoría no encontrada")
        # Verificar subcategorías
        sub_count = db.query(TransactionSubcategory).filter(
            TransactionSubcategory.category_id == category_id
        ).count()
        if sub_count > 0:
            raise HTTPException(
                409, f"No se puede eliminar: tiene {sub_count} subcategoría(s) vinculada(s). Elimínalas primero."
            )
        # TODO M6: verificar transacciones vinculadas
        # tx_count = db.query(Transaction).filter(Transaction.category_id == category_id).count()
        # if tx_count > 0:
        #     raise HTTPException(409, f"No se puede eliminar: tiene {tx_count} transacción(es) vinculada(s). Use desactivar.")
        _log_audit(db, user_id, None, "DELETE_CATEGORY", "transaction_categories", category_id,
                   {"name": cat.name})
        db.delete(cat)
        db.commit()
        return True

    @staticmethod
    def delete_subcategory(db, subcategory_id: int, user_id: int):
        """Elimina una subcategoría solo si no tiene transacciones vinculadas."""
        sub = db.query(TransactionSubcategory).get(subcategory_id)
        if not sub:
            raise HTTPException(404, "Subcategoría no encontrada")
        # TODO M6: verificar transacciones vinculadas
        # tx_count = db.query(Transaction).filter(Transaction.subcategory_id == subcategory_id).count()
        # if tx_count > 0:
        #     raise HTTPException(409, f"No se puede eliminar: tiene {tx_count} transacción(es). Use desactivar.")
        cat_id = sub.category_id
        _log_audit(db, user_id, None, "DELETE_SUBCATEGORY", "transaction_subcategories", subcategory_id,
                   {"name": sub.name, "category_id": cat_id})
        db.delete(sub)
        db.commit()
        return cat_id


# ─────────────────────────────────────────────
# DELETE CONDICIONAL — Empleados, Proveedores, Socios
# (parche toggle_delete_catalogos)
# ─────────────────────────────────────────────

class EmployeeDeleteService:
    @staticmethod
    def delete_employee(db, employee_id: int, user_id: int):
        """Elimina empleado si no tiene transacciones vinculadas.
        Borra historial salarial y desvincula vehículos automáticamente."""
        emp = db.query(Employee).get(employee_id)
        if not emp:
            raise HTTPException(404, "Empleado no encontrado")
        # Verificar transacciones vinculadas (bloquea eliminación)
        tx_count = db.query(Transaction).filter(Transaction.employee_id == employee_id).count()
        if tx_count > 0:
            raise HTTPException(
                409,
                f"No se puede eliminar: el empleado tiene {tx_count} transaccion(es) vinculada(s). Desactívelo en su lugar."
            )
        # Borrar historial salarial (dependencia sin valor sin el empleado)
        db.query(EmployeeSalaryHistory).filter(
            EmployeeSalaryHistory.employee_id == employee_id
        ).delete()
        # Desvincular vehículos donde es conductor habitual
        db.query(Vehicle).filter(
            Vehicle.usual_driver_id == employee_id
        ).update({"usual_driver_id": None})
        _log_audit(db, user_id, None, "DELETE_EMPLOYEE", "employees", employee_id,
                   {"code": emp.code, "full_name": emp.full_name})
        db.delete(emp)
        db.commit()
        return {"detail": f"Empleado '{emp.full_name}' eliminado"}


class SupplierDeleteService:
    @staticmethod
    def delete_supplier(db, supplier_id: int, user_id: int):
        """Elimina proveedor si no tiene transacciones vinculadas."""
        sup = db.query(Supplier).get(supplier_id)
        if not sup:
            raise HTTPException(404, "Proveedor no encontrado")
        tx_count = db.query(Transaction).filter(Transaction.supplier_id == supplier_id).count()
        if tx_count > 0:
            raise HTTPException(
                409,
                f"No se puede eliminar: el proveedor tiene {tx_count} transaccion(es) vinculada(s). Desactívelo en su lugar."
            )
        _log_audit(db, user_id, None, "DELETE_SUPPLIER", "suppliers", supplier_id,
                   {"code": sup.code, "name": sup.name})
        db.delete(sup)
        db.commit()
        return {"detail": f"Proveedor '{sup.name}' eliminado"}


class PartnerDeleteService:
    @staticmethod
    def delete_partner(db, partner_id: int, user_id: int):
        """Elimina socio si no tiene transacciones vinculadas."""
        partner = db.query(Partner).get(partner_id)
        if not partner:
            raise HTTPException(404, "Socio no encontrado")
        tx_count = db.query(Transaction).filter(Transaction.partner_id == partner_id).count()
        if tx_count > 0:
            raise HTTPException(
                409,
                f"No se puede eliminar: el socio tiene {tx_count} transaccion(es) vinculada(s). Desactívelo en su lugar."
            )
        _log_audit(db, user_id, None, "DELETE_PARTNER", "partners", partner_id,
                   {"code": partner.code, "full_name": partner.full_name})
        db.delete(partner)
        db.commit()
        return {"detail": f"Socio '{partner.full_name}' eliminado"}


class CorporateAccountDeleteService:
    @staticmethod
    def delete_account(db, account_id: int, user_id: int):
        """Elimina cuenta corporativa si no tiene retiradas bancarias vinculadas."""
        from app.models.cash_flow import BankWithdrawalRequest
        acc = db.query(CorporateAccount).get(account_id)
        if not acc:
            raise HTTPException(404, "Cuenta corporativa no encontrada")
        wd_count = db.query(BankWithdrawalRequest).filter(
            BankWithdrawalRequest.corporate_account_id == account_id
        ).count()
        if wd_count > 0:
            raise HTTPException(
                409,
                f"No se puede eliminar: tiene {wd_count} retirada(s) bancaria(s) vinculada(s). Desactívela en su lugar."
            )
        _log_audit(db, user_id, None, "DELETE_CORPORATE_ACCOUNT", "corporate_accounts", account_id,
                   {"bank_name": acc.bank_name, "account_number": acc.account_number})
        db.delete(acc)
        db.commit()
        return {"detail": f"Cuenta '{acc.bank_name} - {acc.account_number}' eliminada"}


class VehicleDeleteService:
    @staticmethod
    def delete_vehicle(db, vehicle_id: int, user_id: int):
        """Elimina vehículo si no tiene transacciones vinculadas."""
        v = db.query(Vehicle).get(vehicle_id)
        if not v:
            raise HTTPException(404, "Vehículo no encontrado")
        tx_count = db.query(Transaction).filter(Transaction.vehicle_id == vehicle_id).count()
        if tx_count > 0:
            raise HTTPException(
                409,
                f"No se puede eliminar: tiene {tx_count} transaccion(es) vinculada(s). Desactívelo en su lugar."
            )
        _log_audit(db, user_id, None, "DELETE_VEHICLE", "vehicles", vehicle_id,
                   {"plate": v.plate})
        db.delete(v)
        db.commit()
        return {"detail": f"Vehículo '{v.plate}' eliminado"}
