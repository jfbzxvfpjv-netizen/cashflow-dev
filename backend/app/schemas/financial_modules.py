"""Schemas Pydantic para los módulos financieros especiales (M9)."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, field_validator


# -------- Anticipos y préstamos -------------------------------------------
class AdvanceLoanBase(BaseModel):
    employee_id: int
    type: Literal["advance", "loan"]
    amount: Decimal = Field(..., gt=0)
    concept: str = Field(..., min_length=3)


class AdvanceLoanCreate(AdvanceLoanBase):
    # Campos añadidos en M9 Fase 1 — create ahora registra transacción en caja
    category_id: int
    subcategory_id: int
    project_id: int
    work_id: int


class AdvanceLoanRepay(BaseModel):
    amount: Decimal = Field(..., gt=0)
    concept: Optional[str] = None
    # Campos añadidos en M9 Fase 1 — repay manual crea transacción ingreso
    category_id: int
    subcategory_id: int
    project_id: int
    work_id: int


class AdvanceLoanRepayByPayroll(BaseModel):
    """Schema del endpoint interno /advances-loans/{id}/repay-by-payroll.

    Uso exclusivo del service de nómina (M10) cuando un anticipo se salda
    por descuento en salario. NO crea transacción en caja — la transacción
    de caja es la del pago de nómina reducido.
    """
    amount: Decimal = Field(..., gt=0)


class AdvanceLoanOut(AdvanceLoanBase):
    id: int
    status: str
    amount_repaid: Decimal
    opened_at: datetime
    closed_at: Optional[datetime]
    employee_name: Optional[str] = None
    pending: Optional[Decimal] = None
    # Campos añadidos en M9 Fase 1 — vinculación con transacciones en caja
    creation_transaction_id: Optional[int] = None
    repay_transaction_ids: Optional[List[int]] = None

    class Config:
        from_attributes = True


# -------- Retenciones y depósitos -----------------------------------------
class RetentionDepositBase(BaseModel):
    type: Literal["retention", "deposit"]
    amount: Decimal = Field(..., gt=0)
    concept: str = Field(..., min_length=3)
    supplier_id: Optional[int] = None
    employee_id: Optional[int] = None
    release_date: Optional[date] = None

    @field_validator("supplier_id")
    @classmethod
    def at_least_one_party(cls, v, info):
        return v


class RetentionDepositCreate(RetentionDepositBase):
    # Campos añadidos en M9 Fase 1 Parte C
    # Para 'deposit' son obligatorios (se crea transacción al salir dinero).
    # Para 'retention' pueden venir en None (no se crea transacción al crear).
    # La validación se hace en el service.
    category_id: Optional[int] = None
    subcategory_id: Optional[int] = None
    project_id: Optional[int] = None
    work_id: Optional[int] = None


class RetentionDepositRelease(BaseModel):
    """Body del endpoint PUT /retentions-deposits/{id}/release.

    Siempre crea transacción (egreso si retention, ingreso si deposit), por lo
    que los campos de categorización son obligatorios.
    """
    category_id: int
    subcategory_id: int
    project_id: int
    work_id: int
    concept: Optional[str] = None


class RetentionDepositOut(RetentionDepositBase):
    id: int
    status: str
    # M9 Fase 1 Parte C — vinculación con transacciones en caja
    creation_transaction_id: Optional[int] = None
    release_transaction_id: Optional[int] = None
    released_at: Optional[datetime]
    supplier_name: Optional[str] = None
    employee_name: Optional[str] = None

    class Config:
        from_attributes = True


# -------- Circulantes (floats) --------------------------------------------
class FloatCreate(BaseModel):
    employee_id: int
    amount_given: Decimal = Field(..., gt=0)
    concept: Optional[str] = None
    # M9 Fase 1 Parte D — proyecto/obra para la transacción de apertura.
    # Categoría fija: Circulantes/Apertura_Circulante (resuelta en service).
    project_id: int
    work_id: int


class FloatJustify(BaseModel):
    # M9 Fase 1 Parte D — el service crea dos transacciones (egreso real +
    # ingreso compensatorio). El usuario elige libremente cat/subcat/proyecto/obra
    # del gasto real. La transacción compensatoria usa Circulantes/Liquidacion_Circulante.
    amount: Decimal = Field(..., gt=0)
    category_id: int
    subcategory_id: int
    project_id: int
    work_id: int
    concept: Optional[str] = None


class FloatClose(BaseModel):
    # M9 Fase 1 Parte D — si amount_returned > 0 se crea transacción INGRESO
    # con categoría fija Circulantes/Devolucion_Sobrante. En ese caso
    # project_id y work_id son obligatorios (se valida en service).
    amount_returned: Decimal = Field(..., ge=0)
    project_id: Optional[int] = None
    work_id: Optional[int] = None
    notes: Optional[str] = None


class FloatOut(BaseModel):
    id: int
    employee_id: int
    employee_name: Optional[str]
    amount_given: Decimal
    amount_justified: Decimal
    amount_returned: Decimal
    pending: Decimal
    status: str
    opened_at: datetime
    closed_at: Optional[datetime]
    # M9 Fase 1 Parte D — vinculación con transacciones de caja
    creation_transaction_id: Optional[int] = None
    close_transaction_id: Optional[int] = None

    class Config:
        from_attributes = True


# -------- Pagos fraccionados ----------------------------------------------
class InstallmentCreate(BaseModel):
    total_amount: Decimal = Field(..., gt=0)
    concept: str = Field(..., min_length=3)
    installments_count: int = Field(..., gt=0)
    default_category_id:    Optional[int] = None
    default_subcategory_id: Optional[int] = None
    default_project_id:     Optional[int] = None
    default_work_id:        Optional[int] = None
    supplier_id: Optional[int] = None
    employee_id: Optional[int] = None


class InstallmentPay(BaseModel):
    amount: Decimal = Field(..., gt=0)
    category_id: int
    subcategory_id: int
    project_id: int
    work_id: int


class InstallmentOut(BaseModel):
    id: int
    total_amount: Decimal
    amount_paid: Decimal
    pending: Decimal
    installments_count: int
    installments_paid: int
    concept: str
    status: str
    supplier_id: Optional[int]
    employee_id: Optional[int]
    supplier_name: Optional[str] = None
    employee_name: Optional[str] = None
    default_category_id:    Optional[int] = None
    default_subcategory_id: Optional[int] = None
    default_project_id:     Optional[int] = None
    default_work_id:        Optional[int] = None

    class Config:
        from_attributes = True


# -------- Operaciones en divisa -------------------------------------------
class CurrencyBuy(BaseModel):
    xaf_amount: Decimal = Field(..., gt=0)
    eur_amount: Decimal = Field(..., gt=0)
    exchange_office: str = Field(..., min_length=2)
    category_id: int
    subcategory_id: int
    project_id: int
    work_id: int
    delegacion: Optional[str] = None


class CurrencyDeliver(BaseModel):
    eur_amount: Decimal = Field(..., gt=0)
    xaf_equivalent: Decimal = Field(..., gt=0)
    recipient: str = Field(..., min_length=2)
    delegacion: Optional[str] = None




class CurrencyEdit(BaseModel):
    """Edición de una entrega de euros (dentro de ventana de 15 min nativo
    o 30 días para admin con motivo). Todos los campos opcionales — solo
    se actualizan los que se envíen."""
    eur_amount: Optional[Decimal] = Field(default=None, gt=0)
    xaf_equivalent: Optional[Decimal] = Field(default=None, gt=0)
    recipient: Optional[str] = Field(default=None, min_length=2)
    reason: Optional[str] = None  # obligatorio si admin fuera de ventana


class CurrencyCancel(BaseModel):
    """Anulación de una operación de divisa. Devuelve los euros al stock."""
    reason: str = Field(..., min_length=3)


class CurrencyOperationOut(BaseModel):
    id: int
    delegacion: str
    op_type: str
    xaf_amount: Decimal
    eur_amount: Decimal
    exchange_rate: Decimal
    exchange_office: Optional[str]
    eur_stock_after: Decimal
    buy_transaction_id: Optional[int]
    delivery_transaction_id: Optional[int]
    created_at: datetime
    editable_until: Optional[datetime] = None
    cancelled: bool = False
    cancelled_at: Optional[datetime] = None
    cancel_reason: Optional[str] = None

    class Config:
        from_attributes = True


class EurStockOut(BaseModel):
    delegacion: str
    current_eur_stock: Decimal
    last_updated: Optional[datetime]

    class Config:
        from_attributes = True


# -------- Cuenta corriente de socios --------------------------------------
class PartnerChargeCreate(BaseModel):
    partner_id: int
    amount: Decimal = Field(..., gt=0)
    concept: str = Field(..., min_length=3)
    category_id: int
    subcategory_id: int
    project_id: int
    work_id: int
    delegacion: Optional[str] = None


class PartnerContribution(BaseModel):
    partner_id: int
    amount: Decimal = Field(..., gt=0)
    concept: str
    # M9 Fase 1 Parte E — categorización obligatoria para la transacción ingreso
    category_id: int
    subcategory_id: int
    project_id: int
    work_id: int

class PartnerDividendCompensation(BaseModel):
    partner_id: int
    amount: Decimal = Field(..., gt=0)
    concept: str


class PartnerMovementOut(BaseModel):
    id: int
    partner_id: int
    partner_name: Optional[str]
    type: str
    amount: Decimal
    concept: str
    transaction_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class PartnerBalanceOut(BaseModel):
    partner_id: int
    partner_name: str
    participation_pct: Decimal
    current_balance: Decimal


# -------- Gastos reembolsables --------------------------------------------
class ReimbursableCreate(BaseModel):
    amount_eur: Decimal = Field(..., gt=0)
    amount_xaf: Decimal = Field(..., gt=0)
    payment_method: Literal["tarjeta_personal", "transferencia_personal", "efectivo_personal"]
    concept: str = Field(..., min_length=3)
    category_id: int
    project_id: int
    work_id: int
    subcategory_id: int  # fix reimbursable: subcategoría obligatoria
    partner_id: Optional[int] = None  # fix reimbursable: socio
    employee_id: Optional[int] = None  # fix reimbursable: empleado

class ReimbursableReimburse(BaseModel):
    amount_xaf: Decimal = Field(..., gt=0)
    notes: Optional[str] = None


class ReimbursableOut(BaseModel):
    id: int
    amount_eur: Decimal
    amount_xaf: Decimal
    exchange_rate: Decimal
    payment_method: str
    concept: str
    status: str
    amount_reimbursed: Decimal
    pending_xaf: Decimal
    created_at: datetime
    category_id: int
    project_id: int
    work_id: int
    category_name: Optional[str] = None
    project_name: Optional[str] = None
    work_name: Optional[str] = None

    class Config:
        from_attributes = True


# -------- Envíos de dinero ------------------------------------------------
    # Reembolsable fix: campos nuevos
    partner_id: Optional[int] = None
    partner_name: Optional[str] = None
    employee_id: Optional[int] = None
    employee_name: Optional[str] = None
    subcategory_id: Optional[int] = None
    subcategory_name: Optional[str] = None

class MoneyTransferCreate(BaseModel):
    operator: Literal["western_union", "moneygram", "operador_local"]
    reference_number: str = Field(..., min_length=3)
    sender_name: str = Field(..., min_length=3)
    receiver_name: str = Field(..., min_length=3)
    sender_id: Optional[int] = None
    receiver_id: Optional[int] = None
    amount: Decimal = Field(..., gt=0)
    commission: Decimal = Field(Decimal("0"), ge=0)
    direction: Literal["sent", "received"]
    delegacion_origin: Optional[str] = None
    delegacion_dest: Optional[str] = None
    category_id: int
    subcategory_id: int
    project_id: int
    work_id: int


class MoneyTransferOut(BaseModel):
    id: int
    operator: str
    reference_number: str
    sender_name: str
    receiver_name: str
    sender_id: Optional[int] = None
    receiver_id: Optional[int] = None
    amount: Decimal
    direction: str
    delegacion_origin: Optional[str] = None
    delegacion_dest: Optional[str] = None
    commission_transaction_id: Optional[int] = None
    commission_amount: Optional[Decimal] = None
    operator_label: Optional[str] = None
    direction_label: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class InterDelegationPositionOut(BaseModel):
    bata_to_malabo: Decimal
    malabo_to_bata: Decimal
    net_position: Decimal
    favor_delegation: Optional[str]