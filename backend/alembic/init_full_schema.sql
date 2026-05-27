--
-- PostgreSQL database dump
--


-- Dumped from database version 15.17
-- Dumped by pg_dump version 15.17

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: accounting_periods; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.accounting_periods (
    id integer NOT NULL,
    year integer NOT NULL,
    month integer NOT NULL,
    delegacion character varying(10) NOT NULL,
    closed_at timestamp without time zone,
    closed_by integer NOT NULL,
    total_income numeric(14,2) NOT NULL,
    total_expense numeric(14,2) NOT NULL,
    net_balance numeric(14,2) NOT NULL,
    transaction_count integer NOT NULL,
    notes text,
    CONSTRAINT ck_acct_month CHECK (((month >= 1) AND (month <= 12)))
);


--
-- Name: accounting_periods_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.accounting_periods_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: accounting_periods_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.accounting_periods_id_seq OWNED BY public.accounting_periods.id;


--
-- Name: advances_loans; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.advances_loans (
    id integer NOT NULL,
    employee_id integer NOT NULL,
    type character varying(10) NOT NULL,
    amount numeric(12,2) NOT NULL,
    concept text NOT NULL,
    status character varying(10) DEFAULT 'open'::character varying NOT NULL,
    amount_repaid numeric(12,2) DEFAULT 0 NOT NULL,
    opened_at timestamp without time zone DEFAULT now() NOT NULL,
    closed_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    creation_transaction_id integer,
    repay_transaction_ids integer[] DEFAULT '{}'::integer[] NOT NULL,
    installments_count integer,
    CONSTRAINT advances_loans_amount_check CHECK ((amount > (0)::numeric)),
    CONSTRAINT advances_loans_status_check CHECK (((status)::text = ANY ((ARRAY['open'::character varying, 'partial'::character varying, 'closed'::character varying])::text[]))),
    CONSTRAINT advances_loans_type_check CHECK (((type)::text = ANY ((ARRAY['advance'::character varying, 'loan'::character varying])::text[]))),
    CONSTRAINT ck_loan_installments_count CHECK (((((type)::text = 'advance'::text) AND (installments_count IS NULL)) OR (((type)::text = 'loan'::text) AND (installments_count IS NOT NULL) AND (installments_count >= 1))))
);


--
-- Name: advances_loans_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.advances_loans_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: advances_loans_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.advances_loans_id_seq OWNED BY public.advances_loans.id;


--
-- Name: audit_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.audit_log (
    id integer NOT NULL,
    user_id integer,
    delegacion character varying(10),
    action character varying(60) NOT NULL,
    entity character varying(60) NOT NULL,
    entity_id integer,
    details jsonb,
    ip_address character varying(45),
    access_type character varying(10),
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: audit_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.audit_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: audit_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.audit_log_id_seq OWNED BY public.audit_log.id;


--
-- Name: bank_withdrawal_requests; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.bank_withdrawal_requests (
    id integer NOT NULL,
    delegacion character varying(10) NOT NULL,
    corporate_account_id integer,
    amount numeric(12,2) NOT NULL,
    cheque_reference character varying(100),
    proposed_by integer NOT NULL,
    proposed_at timestamp without time zone,
    approved_by integer,
    approved_at timestamp without time zone,
    confirmed_by integer,
    confirmed_at timestamp without time zone,
    session_id integer,
    status character varying(15),
    rejection_reason text,
    notes text,
    requested_by integer,
    requested_at timestamp without time zone,
    reason text,
    formalized_by integer,
    formalized_at timestamp without time zone,
    CONSTRAINT ck_bw_amount_pos CHECK ((amount > (0)::numeric)),
    CONSTRAINT ck_bw_status CHECK (((status)::text = ANY ((ARRAY['requested'::character varying, 'formalized'::character varying, 'approved'::character varying, 'confirmed'::character varying, 'rejected'::character varying])::text[])))
);


--
-- Name: bank_withdrawal_requests_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.bank_withdrawal_requests_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: bank_withdrawal_requests_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.bank_withdrawal_requests_id_seq OWNED BY public.bank_withdrawal_requests.id;


--
-- Name: cash_counts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cash_counts (
    id integer NOT NULL,
    session_id integer NOT NULL,
    delegacion character varying(10) NOT NULL,
    theoretical_balance numeric(14,2) NOT NULL,
    physical_count numeric(14,2) NOT NULL,
    difference numeric(14,2) NOT NULL,
    notes text,
    counted_by integer NOT NULL,
    counted_at timestamp without time zone DEFAULT now()
);


--
-- Name: cash_counts_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cash_counts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: cash_counts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cash_counts_id_seq OWNED BY public.cash_counts.id;


--
-- Name: cash_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cash_sessions (
    id integer NOT NULL,
    user_id integer NOT NULL,
    delegacion character varying(10) NOT NULL,
    opened_at timestamp without time zone,
    closed_at timestamp without time zone,
    opening_balance numeric(12,2) NOT NULL,
    closing_balance numeric(12,2),
    status character varying(10),
    notes text,
    CONSTRAINT ck_session_deleg CHECK (((delegacion)::text = ANY ((ARRAY['Bata'::character varying, 'Malabo'::character varying])::text[]))),
    CONSTRAINT ck_session_status CHECK (((status)::text = ANY ((ARRAY['open'::character varying, 'closed'::character varying])::text[])))
);


--
-- Name: cash_sessions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cash_sessions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: cash_sessions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cash_sessions_id_seq OWNED BY public.cash_sessions.id;


--
-- Name: category_approval_thresholds; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.category_approval_thresholds (
    id integer NOT NULL,
    category_id integer NOT NULL,
    delegacion character varying(10) NOT NULL,
    threshold_amount numeric(12,2) NOT NULL,
    created_at timestamp without time zone DEFAULT now()
);


--
-- Name: category_approval_thresholds_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.category_approval_thresholds_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: category_approval_thresholds_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.category_approval_thresholds_id_seq OWNED BY public.category_approval_thresholds.id;


--
-- Name: corporate_accounts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.corporate_accounts (
    id integer NOT NULL,
    bank_name character varying(100) NOT NULL,
    account_number character varying(50) NOT NULL,
    account_holder character varying(100) NOT NULL,
    delegacion character varying(10) NOT NULL,
    active boolean,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT ck_corpaccount_delegacion CHECK (((delegacion)::text = ANY ((ARRAY['Bata'::character varying, 'Malabo'::character varying])::text[])))
);


--
-- Name: corporate_accounts_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.corporate_accounts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: corporate_accounts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.corporate_accounts_id_seq OWNED BY public.corporate_accounts.id;


--
-- Name: currency_operations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.currency_operations (
    id integer NOT NULL,
    xaf_amount numeric(14,2) NOT NULL,
    eur_amount numeric(12,2) NOT NULL,
    exchange_rate numeric(10,4) NOT NULL,
    exchange_office character varying(100),
    buy_transaction_id integer,
    delivery_transaction_id integer,
    eur_stock_after numeric(12,2),
    delegacion character varying(10) NOT NULL,
    op_type character varying(10) NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    editable_until timestamp without time zone,
    cancelled boolean DEFAULT false NOT NULL,
    cancelled_at timestamp without time zone,
    cancelled_by_user_id integer,
    cancel_reason text,
    CONSTRAINT currency_operations_delegacion_check CHECK (((delegacion)::text = ANY ((ARRAY['Bata'::character varying, 'Malabo'::character varying])::text[]))),
    CONSTRAINT currency_operations_eur_amount_check CHECK ((eur_amount > (0)::numeric)),
    CONSTRAINT currency_operations_op_type_check CHECK (((op_type)::text = ANY ((ARRAY['buy'::character varying, 'deliver'::character varying])::text[]))),
    CONSTRAINT currency_operations_xaf_amount_check CHECK ((xaf_amount > (0)::numeric))
);


--
-- Name: currency_operations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.currency_operations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: currency_operations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.currency_operations_id_seq OWNED BY public.currency_operations.id;


--
-- Name: employee_fingerprints; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.employee_fingerprints (
    id integer NOT NULL,
    employee_id integer NOT NULL,
    finger_position character varying(20) NOT NULL,
    capture_index smallint NOT NULL,
    template_bytes bytea NOT NULL,
    quality_score smallint,
    created_at timestamp without time zone DEFAULT now(),
    created_by integer NOT NULL,
    CONSTRAINT employee_fingerprints_capture_index_check CHECK (((capture_index >= 1) AND (capture_index <= 4))),
    CONSTRAINT employee_fingerprints_finger_position_check CHECK (((finger_position)::text = ANY ((ARRAY['right_thumb'::character varying, 'right_index'::character varying, 'right_middle'::character varying, 'right_ring'::character varying, 'right_pinky'::character varying, 'left_thumb'::character varying, 'left_index'::character varying, 'left_middle'::character varying, 'left_ring'::character varying, 'left_pinky'::character varying])::text[]))),
    CONSTRAINT employee_fingerprints_quality_score_check CHECK (((quality_score >= 0) AND (quality_score <= 100)))
);


--
-- Name: employee_fingerprints_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.employee_fingerprints_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: employee_fingerprints_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.employee_fingerprints_id_seq OWNED BY public.employee_fingerprints.id;


--
-- Name: employee_salary_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.employee_salary_history (
    id integer NOT NULL,
    employee_id integer NOT NULL,
    salary_gross numeric(12,2) NOT NULL,
    salary_transfer numeric(12,2) NOT NULL,
    effective_date date NOT NULL,
    created_by integer NOT NULL,
    created_at timestamp without time zone DEFAULT now()
);


--
-- Name: employee_salary_history_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.employee_salary_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: employee_salary_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.employee_salary_history_id_seq OWNED BY public.employee_salary_history.id;


--
-- Name: employees; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.employees (
    id integer NOT NULL,
    code character varying(30) NOT NULL,
    full_name character varying(100) NOT NULL,
    department character varying(100),
    "position" character varying(100),
    delegacion character varying(10) NOT NULL,
    salary_gross numeric(12,2) NOT NULL,
    salary_transfer numeric(12,2) NOT NULL,
    salary_effective_date date NOT NULL,
    advance_pending boolean,
    advance_amount numeric(12,2),
    active boolean,
    created_at timestamp without time zone DEFAULT now(),
    user_id integer,
    CONSTRAINT ck_employee_delegacion CHECK (((delegacion)::text = ANY ((ARRAY['Bata'::character varying, 'Malabo'::character varying])::text[])))
);


--
-- Name: employees_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.employees_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: employees_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.employees_id_seq OWNED BY public.employees.id;


--
-- Name: eur_stock; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.eur_stock (
    id integer NOT NULL,
    delegacion character varying(10) NOT NULL,
    current_eur_stock numeric(12,2) DEFAULT 0 NOT NULL,
    last_updated timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT eur_stock_delegacion_check CHECK (((delegacion)::text = ANY ((ARRAY['Bata'::character varying, 'Malabo'::character varying])::text[])))
);


--
-- Name: eur_stock_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.eur_stock_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: eur_stock_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.eur_stock_id_seq OWNED BY public.eur_stock.id;


--
-- Name: expense_approvals; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.expense_approvals (
    id integer NOT NULL,
    transaction_id integer NOT NULL,
    requested_by integer NOT NULL,
    requested_at timestamp without time zone DEFAULT now(),
    approved_by integer,
    approved_at timestamp without time zone,
    status character varying(15) NOT NULL,
    rejection_reason text
);


--
-- Name: expense_approvals_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.expense_approvals_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: expense_approvals_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.expense_approvals_id_seq OWNED BY public.expense_approvals.id;


--
-- Name: float_justifications; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.float_justifications (
    id integer NOT NULL,
    float_id integer NOT NULL,
    transaction_id integer NOT NULL,
    amount numeric(12,2) NOT NULL,
    justified_at timestamp without time zone DEFAULT now() NOT NULL,
    expense_transaction_id integer,
    compensation_transaction_id integer,
    CONSTRAINT float_justifications_amount_check CHECK ((amount > (0)::numeric))
);


--
-- Name: float_justifications_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.float_justifications_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: float_justifications_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.float_justifications_id_seq OWNED BY public.float_justifications.id;


--
-- Name: floats; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.floats (
    id integer NOT NULL,
    employee_id integer NOT NULL,
    amount_given numeric(12,2) NOT NULL,
    amount_justified numeric(12,2) DEFAULT 0 NOT NULL,
    amount_returned numeric(12,2) DEFAULT 0 NOT NULL,
    status character varying(10) DEFAULT 'open'::character varying NOT NULL,
    opened_at timestamp without time zone DEFAULT now() NOT NULL,
    closed_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    creation_transaction_id integer,
    close_transaction_id integer,
    CONSTRAINT floats_amount_given_check CHECK ((amount_given > (0)::numeric)),
    CONSTRAINT floats_status_check CHECK (((status)::text = ANY ((ARRAY['open'::character varying, 'partial'::character varying, 'closed'::character varying])::text[])))
);


--
-- Name: floats_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.floats_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: floats_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.floats_id_seq OWNED BY public.floats.id;


--
-- Name: import_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.import_history (
    id integer NOT NULL,
    delegacion character varying(10) NOT NULL,
    filename character varying(255) NOT NULL,
    session_id integer NOT NULL,
    rows_imported integer NOT NULL,
    rows_skipped integer NOT NULL,
    projects_created integer NOT NULL,
    works_created integer NOT NULL,
    imported_by integer NOT NULL,
    imported_at timestamp without time zone DEFAULT now()
);


--
-- Name: import_history_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.import_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: import_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.import_history_id_seq OWNED BY public.import_history.id;


--
-- Name: installment_payments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.installment_payments (
    id integer NOT NULL,
    total_amount numeric(12,2) NOT NULL,
    concept text NOT NULL,
    supplier_id integer,
    employee_id integer,
    amount_paid numeric(12,2) DEFAULT 0 NOT NULL,
    installments_count integer DEFAULT 0 NOT NULL,
    status character varying(10) DEFAULT 'active'::character varying NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    default_category_id integer,
    default_subcategory_id integer,
    default_project_id integer,
    default_work_id integer,
    CONSTRAINT installment_payments_check CHECK (((supplier_id IS NOT NULL) OR (employee_id IS NOT NULL))),
    CONSTRAINT installment_payments_status_check CHECK (((status)::text = ANY ((ARRAY['active'::character varying, 'closed'::character varying])::text[]))),
    CONSTRAINT installment_payments_total_amount_check CHECK ((total_amount > (0)::numeric))
);


--
-- Name: installment_payments_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.installment_payments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: installment_payments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.installment_payments_id_seq OWNED BY public.installment_payments.id;


--
-- Name: installment_records; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.installment_records (
    id integer NOT NULL,
    installment_payment_id integer NOT NULL,
    transaction_id integer NOT NULL,
    amount numeric(12,2) NOT NULL,
    paid_at timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT installment_records_amount_check CHECK ((amount > (0)::numeric))
);


--
-- Name: installment_records_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.installment_records_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: installment_records_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.installment_records_id_seq OWNED BY public.installment_records.id;


--
-- Name: money_transfers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.money_transfers (
    id integer NOT NULL,
    operator character varying(20) NOT NULL,
    reference_number character varying(50),
    sender_name character varying(150) NOT NULL,
    receiver_name character varying(150) NOT NULL,
    sender_id integer,
    receiver_id integer,
    amount numeric(14,2) NOT NULL,
    commission_transaction_id integer,
    main_transaction_id integer,
    direction character varying(10) NOT NULL,
    delegacion_origin character varying(10),
    delegacion_dest character varying(10),
    created_by integer NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT money_transfers_amount_check CHECK ((amount > (0)::numeric)),
    CONSTRAINT money_transfers_delegacion_dest_check CHECK (((delegacion_dest)::text = ANY ((ARRAY['Bata'::character varying, 'Malabo'::character varying])::text[]))),
    CONSTRAINT money_transfers_delegacion_origin_check CHECK (((delegacion_origin)::text = ANY ((ARRAY['Bata'::character varying, 'Malabo'::character varying])::text[]))),
    CONSTRAINT money_transfers_direction_check CHECK (((direction)::text = ANY ((ARRAY['sent'::character varying, 'received'::character varying])::text[]))),
    CONSTRAINT money_transfers_operator_check CHECK (((operator)::text = ANY ((ARRAY['western_union'::character varying, 'moneygram'::character varying, 'operador_local'::character varying])::text[])))
);


--
-- Name: money_transfers_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.money_transfers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: money_transfers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.money_transfers_id_seq OWNED BY public.money_transfers.id;


--
-- Name: partner_account_movements; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.partner_account_movements (
    id integer NOT NULL,
    partner_id integer NOT NULL,
    type character varying(25) NOT NULL,
    amount numeric(14,2) NOT NULL,
    concept text NOT NULL,
    transaction_id integer,
    created_by integer NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT partner_account_movements_amount_check CHECK ((amount > (0)::numeric)),
    CONSTRAINT partner_account_movements_type_check CHECK (((type)::text = ANY ((ARRAY['charge'::character varying, 'contribution'::character varying, 'dividend_compensation'::character varying])::text[])))
);


--
-- Name: partner_account_movements_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.partner_account_movements_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: partner_account_movements_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.partner_account_movements_id_seq OWNED BY public.partner_account_movements.id;


--
-- Name: partners; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.partners (
    id integer NOT NULL,
    code character varying(10) NOT NULL,
    full_name character varying(100) NOT NULL,
    participation_pct numeric(5,2) NOT NULL,
    can_contribute boolean,
    current_balance numeric(14,2) NOT NULL,
    active boolean,
    created_at timestamp without time zone DEFAULT now()
);


--
-- Name: partners_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.partners_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: partners_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.partners_id_seq OWNED BY public.partners.id;


--
-- Name: payroll_entries; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.payroll_entries (
    id integer NOT NULL,
    period_id integer NOT NULL,
    employee_id integer NOT NULL,
    salary_gross numeric(12,2) NOT NULL,
    salary_transfer numeric(12,2) NOT NULL,
    cash_amount numeric(12,2) NOT NULL,
    transaction_id integer,
    paid_at timestamp without time zone,
    notes text,
    deduction_advances numeric(12,2) DEFAULT 0 NOT NULL,
    deduction_loans numeric(12,2) DEFAULT 0 NOT NULL,
    deduction_installments numeric(12,2) DEFAULT 0 NOT NULL,
    deduction_retentions numeric(12,2) DEFAULT 0 NOT NULL,
    deduction_refs jsonb DEFAULT '{}'::jsonb NOT NULL,
    manual_override boolean DEFAULT false NOT NULL,
    liquidated_without_cash boolean DEFAULT false NOT NULL,
    liquidated_at timestamp without time zone,
    liquidated_by integer,
    CONSTRAINT ck_payroll_entry_amounts CHECK ((cash_amount >= (0)::numeric))
);


--
-- Name: payroll_entries_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.payroll_entries_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: payroll_entries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.payroll_entries_id_seq OWNED BY public.payroll_entries.id;


--
-- Name: payroll_periods; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.payroll_periods (
    id integer NOT NULL,
    year smallint NOT NULL,
    month smallint NOT NULL,
    delegacion character varying(10) NOT NULL,
    status character varying(20) DEFAULT 'draft'::character varying NOT NULL,
    created_by integer NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    paid_at timestamp without time zone,
    notes text,
    CONSTRAINT ck_payroll_deleg CHECK (((delegacion)::text = ANY ((ARRAY['Bata'::character varying, 'Malabo'::character varying])::text[]))),
    CONSTRAINT ck_payroll_month CHECK (((month >= 1) AND (month <= 12))),
    CONSTRAINT ck_payroll_status CHECK (((status)::text = ANY ((ARRAY['draft'::character varying, 'paid'::character varying])::text[])))
);


--
-- Name: payroll_periods_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.payroll_periods_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: payroll_periods_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.payroll_periods_id_seq OWNED BY public.payroll_periods.id;


--
-- Name: projects; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.projects (
    id integer NOT NULL,
    code character varying(30) NOT NULL,
    name character varying(150) NOT NULL,
    description text,
    active boolean,
    created_at timestamp without time zone DEFAULT now()
);


--
-- Name: projects_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.projects_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: projects_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.projects_id_seq OWNED BY public.projects.id;


--
-- Name: reimbursable_expenses; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.reimbursable_expenses (
    id integer NOT NULL,
    amount_eur numeric(12,2) NOT NULL,
    amount_xaf numeric(14,2) NOT NULL,
    exchange_rate numeric(10,4) NOT NULL,
    payment_method character varying(30) NOT NULL,
    concept text NOT NULL,
    category_id integer NOT NULL,
    project_id integer,
    work_id integer,
    status character varying(15) DEFAULT 'pending'::character varying NOT NULL,
    amount_reimbursed numeric(14,2) DEFAULT 0 NOT NULL,
    created_by integer NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    partner_id integer,
    employee_id integer,
    subcategory_id integer,
    CONSTRAINT reimbursable_expenses_amount_eur_check CHECK ((amount_eur > (0)::numeric)),
    CONSTRAINT reimbursable_expenses_amount_xaf_check CHECK ((amount_xaf > (0)::numeric)),
    CONSTRAINT reimbursable_expenses_payment_method_check CHECK (((payment_method)::text = ANY ((ARRAY['tarjeta_personal'::character varying, 'transferencia_personal'::character varying, 'efectivo_personal'::character varying])::text[]))),
    CONSTRAINT reimbursable_expenses_status_check CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'partial'::character varying, 'reimbursed'::character varying])::text[])))
);


--
-- Name: reimbursable_expenses_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.reimbursable_expenses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: reimbursable_expenses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.reimbursable_expenses_id_seq OWNED BY public.reimbursable_expenses.id;


--
-- Name: retentions_deposits; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.retentions_deposits (
    id integer NOT NULL,
    supplier_id integer,
    employee_id integer,
    type character varying(15) NOT NULL,
    amount numeric(12,2) NOT NULL,
    concept text NOT NULL,
    status character varying(10) DEFAULT 'pending'::character varying NOT NULL,
    release_date date,
    released_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    creation_transaction_id integer,
    release_transaction_id integer,
    CONSTRAINT retentions_deposits_amount_check CHECK ((amount > (0)::numeric)),
    CONSTRAINT retentions_deposits_check CHECK (((supplier_id IS NOT NULL) OR (employee_id IS NOT NULL))),
    CONSTRAINT retentions_deposits_status_check CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'released'::character varying])::text[]))),
    CONSTRAINT retentions_deposits_type_check CHECK (((type)::text = ANY ((ARRAY['retention'::character varying, 'deposit'::character varying])::text[])))
);


--
-- Name: retentions_deposits_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.retentions_deposits_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: retentions_deposits_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.retentions_deposits_id_seq OWNED BY public.retentions_deposits.id;


--
-- Name: suppliers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.suppliers (
    id integer NOT NULL,
    code character varying(30) NOT NULL,
    name character varying(150) NOT NULL,
    supplier_type character varying(20) NOT NULL,
    tax_id character varying(50),
    contact_name character varying(100),
    phone character varying(30),
    email character varying(150),
    active boolean,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT ck_supplier_type CHECK (((supplier_type)::text = ANY ((ARRAY['empresa'::character varying, 'organismo'::character varying, 'aerolinea'::character varying, 'gasolinera'::character varying, 'banco'::character varying, 'otro'::character varying])::text[])))
);


--
-- Name: suppliers_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.suppliers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: suppliers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.suppliers_id_seq OWNED BY public.suppliers.id;


--
-- Name: system_config; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.system_config (
    id integer NOT NULL,
    delegacion character varying(10) NOT NULL,
    opening_balance numeric(14,2) NOT NULL,
    opening_balance_date date NOT NULL,
    currency character varying(5),
    organization_name character varying(150) NOT NULL,
    configured_by integer NOT NULL,
    configured_at timestamp without time zone,
    last_modified_by integer,
    last_modified_at timestamp without time zone,
    CONSTRAINT ck_sysconfig_deleg CHECK (((delegacion)::text = ANY ((ARRAY['Bata'::character varying, 'Malabo'::character varying])::text[])))
);


--
-- Name: system_config_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.system_config_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: system_config_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.system_config_id_seq OWNED BY public.system_config.id;


--
-- Name: transaction_attachments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.transaction_attachments (
    id integer NOT NULL,
    transaction_id integer NOT NULL,
    original_filename character varying(255) NOT NULL,
    stored_filename character varying(255) NOT NULL,
    mime_type character varying(100),
    file_size_bytes integer,
    file_path character varying(500) NOT NULL,
    uploaded_by integer NOT NULL,
    uploaded_at timestamp without time zone,
    locked boolean,
    kind character varying(20),
    sha256_hash character varying(64),
    CONSTRAINT chk_attachment_kind CHECK (((kind IS NULL) OR ((kind)::text = ANY ((ARRAY['invoice'::character varying, 'receipt'::character varying, 'photo'::character varying, 'other'::character varying])::text[]))))
);


--
-- Name: transaction_attachments_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.transaction_attachments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: transaction_attachments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.transaction_attachments_id_seq OWNED BY public.transaction_attachments.id;


--
-- Name: transaction_categories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.transaction_categories (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    type character varying(10) NOT NULL,
    requires_attachment boolean,
    active boolean,
    created_at timestamp without time zone DEFAULT now(),
    counterparty_type character varying(20) DEFAULT 'external'::character varying NOT NULL,
    requires_vehicle boolean DEFAULT false NOT NULL,
    CONSTRAINT ck_category_type CHECK (((type)::text = ANY ((ARRAY['income'::character varying, 'expense'::character varying, 'both'::character varying])::text[]))),
    CONSTRAINT ck_counterparty_type CHECK (((counterparty_type)::text = ANY ((ARRAY['employee'::character varying, 'supplier'::character varying, 'partner'::character varying, 'external'::character varying, 'any'::character varying, 'none'::character varying])::text[])))
);


--
-- Name: transaction_categories_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.transaction_categories_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: transaction_categories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.transaction_categories_id_seq OWNED BY public.transaction_categories.id;


--
-- Name: transaction_projects; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.transaction_projects (
    id integer NOT NULL,
    transaction_id integer NOT NULL,
    project_id integer NOT NULL,
    work_id integer
);


--
-- Name: transaction_projects_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.transaction_projects_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: transaction_projects_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.transaction_projects_id_seq OWNED BY public.transaction_projects.id;


--
-- Name: transaction_signatures; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.transaction_signatures (
    id integer NOT NULL,
    transaction_id integer NOT NULL,
    signer_type character varying(20) NOT NULL,
    signer_name character varying(100) NOT NULL,
    signature_data text,
    signed_at timestamp without time zone,
    status character varying(15),
    employee_id integer,
    supplier_id integer,
    partner_id integer,
    sha256_hash character varying(64),
    device_model character varying(50),
    width_px integer,
    height_px integer,
    duration_ms integer,
    fss_data bytea,
    captured_by_user_id integer,
    signature_method character varying(30) DEFAULT 'wacom'::character varying NOT NULL,
    fingerprint_finger_position character varying(20),
    fingerprint_score smallint,
    fingerprint_attempts smallint,
    fingerprint_failed_scores text,
    signer_user_id integer,
    CONSTRAINT chk_fingerprint_score_range CHECK (((fingerprint_score IS NULL) OR ((fingerprint_score >= 0) AND (fingerprint_score <= 100)))),
    CONSTRAINT chk_signature_method_consistency CHECK (((((signature_method)::text = ANY ((ARRAY['wacom'::character varying, 'wacom_provisional'::character varying])::text[])) AND (signature_data IS NOT NULL) AND (sha256_hash IS NOT NULL)) OR (((signature_method)::text = 'fingerprint'::text) AND (fingerprint_score IS NOT NULL) AND (fingerprint_finger_position IS NOT NULL) AND (signer_user_id IS NOT NULL)))),
    CONSTRAINT chk_signature_method_valid CHECK (((signature_method)::text = ANY ((ARRAY['wacom'::character varying, 'fingerprint'::character varying, 'wacom_provisional'::character varying])::text[]))),
    CONSTRAINT chk_signature_status CHECK (((status IS NULL) OR ((status)::text = ANY ((ARRAY['valid'::character varying, 'provisional'::character varying])::text[]))))
);


--
-- Name: transaction_signatures_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.transaction_signatures_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: transaction_signatures_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.transaction_signatures_id_seq OWNED BY public.transaction_signatures.id;


--
-- Name: transaction_subcategories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.transaction_subcategories (
    id integer NOT NULL,
    category_id integer NOT NULL,
    name character varying(100) NOT NULL,
    active boolean,
    created_at timestamp without time zone DEFAULT now()
);


--
-- Name: transaction_subcategories_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.transaction_subcategories_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: transaction_subcategories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.transaction_subcategories_id_seq OWNED BY public.transaction_subcategories.id;


--
-- Name: transactions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.transactions (
    id integer NOT NULL,
    session_id integer NOT NULL,
    delegacion character varying(10) NOT NULL,
    category_id integer NOT NULL,
    subcategory_id integer NOT NULL,
    user_id integer NOT NULL,
    supplier_id integer,
    employee_id integer,
    partner_id integer,
    counterparty_free character varying(150),
    vehicle_id integer,
    type character varying(10) NOT NULL,
    amount numeric(12,2) NOT NULL,
    concept text NOT NULL,
    reference_number character varying(10) NOT NULL,
    transaction_type character varying(20),
    cancelled boolean,
    cancel_ref_id integer,
    is_adjustment boolean,
    adjustment_ref_period integer,
    approval_status character varying(20),
    approved_by integer,
    approved_at timestamp without time zone,
    imported boolean,
    import_source character varying(255),
    imported_editable_until timestamp without time zone,
    editable_until timestamp without time zone NOT NULL,
    integrity_hash character varying(64) NOT NULL,
    created_at timestamp without time zone,
    CONSTRAINT ck_tx_amount_pos CHECK ((amount > (0)::numeric)),
    CONSTRAINT ck_tx_approval CHECK (((approval_status)::text = ANY (ARRAY[('approved'::character varying)::text, ('pending_approval'::character varying)::text, ('rejected'::character varying)::text]))),
    CONSTRAINT ck_tx_type CHECK (((type)::text = ANY ((ARRAY['income'::character varying, 'expense'::character varying])::text[])))
);


--
-- Name: transactions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.transactions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: transactions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.transactions_id_seq OWNED BY public.transactions.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(50) NOT NULL,
    password_hash character varying(255) NOT NULL,
    full_name character varying(100) NOT NULL,
    role character varying(20) NOT NULL,
    delegacion character varying(10) NOT NULL,
    totp_secret character varying(64),
    totp_enabled boolean,
    totp_recovery_codes character varying[],
    active boolean,
    last_login timestamp with time zone,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: vehicles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.vehicles (
    id integer NOT NULL,
    plate character varying(20) NOT NULL,
    brand character varying(50),
    model character varying(50),
    year integer,
    delegacion character varying(10) NOT NULL,
    usual_driver_id integer,
    active boolean,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT ck_vehicle_delegacion CHECK (((delegacion)::text = ANY ((ARRAY['Bata'::character varying, 'Malabo'::character varying])::text[])))
);


--
-- Name: vehicles_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.vehicles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: vehicles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.vehicles_id_seq OWNED BY public.vehicles.id;


--
-- Name: works; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.works (
    id integer NOT NULL,
    project_id integer NOT NULL,
    code character varying(50) NOT NULL,
    name character varying(150) NOT NULL,
    active boolean,
    created_at timestamp without time zone DEFAULT now()
);


--
-- Name: works_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.works_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: works_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.works_id_seq OWNED BY public.works.id;


--
-- Name: accounting_periods id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.accounting_periods ALTER COLUMN id SET DEFAULT nextval('public.accounting_periods_id_seq'::regclass);


--
-- Name: advances_loans id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.advances_loans ALTER COLUMN id SET DEFAULT nextval('public.advances_loans_id_seq'::regclass);


--
-- Name: audit_log id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_log ALTER COLUMN id SET DEFAULT nextval('public.audit_log_id_seq'::regclass);


--
-- Name: bank_withdrawal_requests id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bank_withdrawal_requests ALTER COLUMN id SET DEFAULT nextval('public.bank_withdrawal_requests_id_seq'::regclass);


--
-- Name: cash_counts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cash_counts ALTER COLUMN id SET DEFAULT nextval('public.cash_counts_id_seq'::regclass);


--
-- Name: cash_sessions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cash_sessions ALTER COLUMN id SET DEFAULT nextval('public.cash_sessions_id_seq'::regclass);


--
-- Name: category_approval_thresholds id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.category_approval_thresholds ALTER COLUMN id SET DEFAULT nextval('public.category_approval_thresholds_id_seq'::regclass);


--
-- Name: corporate_accounts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.corporate_accounts ALTER COLUMN id SET DEFAULT nextval('public.corporate_accounts_id_seq'::regclass);


--
-- Name: currency_operations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.currency_operations ALTER COLUMN id SET DEFAULT nextval('public.currency_operations_id_seq'::regclass);


--
-- Name: employee_fingerprints id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_fingerprints ALTER COLUMN id SET DEFAULT nextval('public.employee_fingerprints_id_seq'::regclass);


--
-- Name: employee_salary_history id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_salary_history ALTER COLUMN id SET DEFAULT nextval('public.employee_salary_history_id_seq'::regclass);


--
-- Name: employees id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employees ALTER COLUMN id SET DEFAULT nextval('public.employees_id_seq'::regclass);


--
-- Name: eur_stock id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.eur_stock ALTER COLUMN id SET DEFAULT nextval('public.eur_stock_id_seq'::regclass);


--
-- Name: expense_approvals id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expense_approvals ALTER COLUMN id SET DEFAULT nextval('public.expense_approvals_id_seq'::regclass);


--
-- Name: float_justifications id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.float_justifications ALTER COLUMN id SET DEFAULT nextval('public.float_justifications_id_seq'::regclass);


--
-- Name: floats id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.floats ALTER COLUMN id SET DEFAULT nextval('public.floats_id_seq'::regclass);


--
-- Name: import_history id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.import_history ALTER COLUMN id SET DEFAULT nextval('public.import_history_id_seq'::regclass);


--
-- Name: installment_payments id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.installment_payments ALTER COLUMN id SET DEFAULT nextval('public.installment_payments_id_seq'::regclass);


--
-- Name: installment_records id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.installment_records ALTER COLUMN id SET DEFAULT nextval('public.installment_records_id_seq'::regclass);


--
-- Name: money_transfers id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.money_transfers ALTER COLUMN id SET DEFAULT nextval('public.money_transfers_id_seq'::regclass);


--
-- Name: partner_account_movements id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.partner_account_movements ALTER COLUMN id SET DEFAULT nextval('public.partner_account_movements_id_seq'::regclass);


--
-- Name: partners id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.partners ALTER COLUMN id SET DEFAULT nextval('public.partners_id_seq'::regclass);


--
-- Name: payroll_entries id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payroll_entries ALTER COLUMN id SET DEFAULT nextval('public.payroll_entries_id_seq'::regclass);


--
-- Name: payroll_periods id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payroll_periods ALTER COLUMN id SET DEFAULT nextval('public.payroll_periods_id_seq'::regclass);


--
-- Name: projects id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects ALTER COLUMN id SET DEFAULT nextval('public.projects_id_seq'::regclass);


--
-- Name: reimbursable_expenses id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reimbursable_expenses ALTER COLUMN id SET DEFAULT nextval('public.reimbursable_expenses_id_seq'::regclass);


--
-- Name: retentions_deposits id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.retentions_deposits ALTER COLUMN id SET DEFAULT nextval('public.retentions_deposits_id_seq'::regclass);


--
-- Name: suppliers id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.suppliers ALTER COLUMN id SET DEFAULT nextval('public.suppliers_id_seq'::regclass);


--
-- Name: system_config id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_config ALTER COLUMN id SET DEFAULT nextval('public.system_config_id_seq'::regclass);


--
-- Name: transaction_attachments id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transaction_attachments ALTER COLUMN id SET DEFAULT nextval('public.transaction_attachments_id_seq'::regclass);


--
-- Name: transaction_categories id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transaction_categories ALTER COLUMN id SET DEFAULT nextval('public.transaction_categories_id_seq'::regclass);


--
-- Name: transaction_projects id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transaction_projects ALTER COLUMN id SET DEFAULT nextval('public.transaction_projects_id_seq'::regclass);


--
-- Name: transaction_signatures id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transaction_signatures ALTER COLUMN id SET DEFAULT nextval('public.transaction_signatures_id_seq'::regclass);


--
-- Name: transaction_subcategories id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transaction_subcategories ALTER COLUMN id SET DEFAULT nextval('public.transaction_subcategories_id_seq'::regclass);


--
-- Name: transactions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions ALTER COLUMN id SET DEFAULT nextval('public.transactions_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: vehicles id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vehicles ALTER COLUMN id SET DEFAULT nextval('public.vehicles_id_seq'::regclass);


--
-- Name: works id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.works ALTER COLUMN id SET DEFAULT nextval('public.works_id_seq'::regclass);


--
-- Name: accounting_periods accounting_periods_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.accounting_periods
    ADD CONSTRAINT accounting_periods_pkey PRIMARY KEY (id);


--
-- Name: advances_loans advances_loans_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.advances_loans
    ADD CONSTRAINT advances_loans_pkey PRIMARY KEY (id);


--
-- Name: audit_log audit_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_log
    ADD CONSTRAINT audit_log_pkey PRIMARY KEY (id);


--
-- Name: bank_withdrawal_requests bank_withdrawal_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bank_withdrawal_requests
    ADD CONSTRAINT bank_withdrawal_requests_pkey PRIMARY KEY (id);


--
-- Name: cash_counts cash_counts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cash_counts
    ADD CONSTRAINT cash_counts_pkey PRIMARY KEY (id);


--
-- Name: cash_sessions cash_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cash_sessions
    ADD CONSTRAINT cash_sessions_pkey PRIMARY KEY (id);


--
-- Name: category_approval_thresholds category_approval_thresholds_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.category_approval_thresholds
    ADD CONSTRAINT category_approval_thresholds_pkey PRIMARY KEY (id);


--
-- Name: corporate_accounts corporate_accounts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.corporate_accounts
    ADD CONSTRAINT corporate_accounts_pkey PRIMARY KEY (id);


--
-- Name: currency_operations currency_operations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.currency_operations
    ADD CONSTRAINT currency_operations_pkey PRIMARY KEY (id);


--
-- Name: employee_fingerprints employee_fingerprints_employee_id_finger_position_capture_i_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_fingerprints
    ADD CONSTRAINT employee_fingerprints_employee_id_finger_position_capture_i_key UNIQUE (employee_id, finger_position, capture_index);


--
-- Name: employee_fingerprints employee_fingerprints_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_fingerprints
    ADD CONSTRAINT employee_fingerprints_pkey PRIMARY KEY (id);


--
-- Name: employee_salary_history employee_salary_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_salary_history
    ADD CONSTRAINT employee_salary_history_pkey PRIMARY KEY (id);


--
-- Name: employees employees_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employees
    ADD CONSTRAINT employees_code_key UNIQUE (code);


--
-- Name: employees employees_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employees
    ADD CONSTRAINT employees_pkey PRIMARY KEY (id);


--
-- Name: eur_stock eur_stock_delegacion_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.eur_stock
    ADD CONSTRAINT eur_stock_delegacion_key UNIQUE (delegacion);


--
-- Name: eur_stock eur_stock_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.eur_stock
    ADD CONSTRAINT eur_stock_pkey PRIMARY KEY (id);


--
-- Name: expense_approvals expense_approvals_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expense_approvals
    ADD CONSTRAINT expense_approvals_pkey PRIMARY KEY (id);


--
-- Name: float_justifications float_justifications_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.float_justifications
    ADD CONSTRAINT float_justifications_pkey PRIMARY KEY (id);


--
-- Name: floats floats_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.floats
    ADD CONSTRAINT floats_pkey PRIMARY KEY (id);


--
-- Name: import_history import_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.import_history
    ADD CONSTRAINT import_history_pkey PRIMARY KEY (id);


--
-- Name: installment_payments installment_payments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.installment_payments
    ADD CONSTRAINT installment_payments_pkey PRIMARY KEY (id);


--
-- Name: installment_records installment_records_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.installment_records
    ADD CONSTRAINT installment_records_pkey PRIMARY KEY (id);


--
-- Name: money_transfers money_transfers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.money_transfers
    ADD CONSTRAINT money_transfers_pkey PRIMARY KEY (id);


--
-- Name: partner_account_movements partner_account_movements_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.partner_account_movements
    ADD CONSTRAINT partner_account_movements_pkey PRIMARY KEY (id);


--
-- Name: partners partners_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.partners
    ADD CONSTRAINT partners_code_key UNIQUE (code);


--
-- Name: partners partners_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.partners
    ADD CONSTRAINT partners_pkey PRIMARY KEY (id);


--
-- Name: payroll_entries payroll_entries_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payroll_entries
    ADD CONSTRAINT payroll_entries_pkey PRIMARY KEY (id);


--
-- Name: payroll_periods payroll_periods_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payroll_periods
    ADD CONSTRAINT payroll_periods_pkey PRIMARY KEY (id);


--
-- Name: projects projects_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_code_key UNIQUE (code);


--
-- Name: projects projects_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_pkey PRIMARY KEY (id);


--
-- Name: reimbursable_expenses reimbursable_expenses_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reimbursable_expenses
    ADD CONSTRAINT reimbursable_expenses_pkey PRIMARY KEY (id);


--
-- Name: retentions_deposits retentions_deposits_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.retentions_deposits
    ADD CONSTRAINT retentions_deposits_pkey PRIMARY KEY (id);


--
-- Name: suppliers suppliers_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.suppliers
    ADD CONSTRAINT suppliers_code_key UNIQUE (code);


--
-- Name: suppliers suppliers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.suppliers
    ADD CONSTRAINT suppliers_pkey PRIMARY KEY (id);


--
-- Name: system_config system_config_delegacion_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_config
    ADD CONSTRAINT system_config_delegacion_key UNIQUE (delegacion);


--
-- Name: system_config system_config_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_config
    ADD CONSTRAINT system_config_pkey PRIMARY KEY (id);


--
-- Name: transaction_attachments transaction_attachments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transaction_attachments
    ADD CONSTRAINT transaction_attachments_pkey PRIMARY KEY (id);


--
-- Name: transaction_categories transaction_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transaction_categories
    ADD CONSTRAINT transaction_categories_pkey PRIMARY KEY (id);


--
-- Name: transaction_projects transaction_projects_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transaction_projects
    ADD CONSTRAINT transaction_projects_pkey PRIMARY KEY (id);


--
-- Name: transaction_signatures transaction_signatures_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transaction_signatures
    ADD CONSTRAINT transaction_signatures_pkey PRIMARY KEY (id);


--
-- Name: transaction_subcategories transaction_subcategories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transaction_subcategories
    ADD CONSTRAINT transaction_subcategories_pkey PRIMARY KEY (id);


--
-- Name: transactions transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_pkey PRIMARY KEY (id);


--
-- Name: transactions transactions_reference_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_reference_number_key UNIQUE (reference_number);


--
-- Name: accounting_periods uq_acct_period; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.accounting_periods
    ADD CONSTRAINT uq_acct_period UNIQUE (year, month, delegacion);


--
-- Name: payroll_entries uq_payroll_entry_period_employee; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payroll_entries
    ADD CONSTRAINT uq_payroll_entry_period_employee UNIQUE (period_id, employee_id);


--
-- Name: payroll_periods uq_payroll_year_month_deleg; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payroll_periods
    ADD CONSTRAINT uq_payroll_year_month_deleg UNIQUE (year, month, delegacion);


--
-- Name: transaction_subcategories uq_subcategory_category_name; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transaction_subcategories
    ADD CONSTRAINT uq_subcategory_category_name UNIQUE (category_id, name);


--
-- Name: transaction_projects uq_tx_proj_work; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transaction_projects
    ADD CONSTRAINT uq_tx_proj_work UNIQUE (transaction_id, project_id, work_id);


--
-- Name: transaction_signatures uq_tx_signer; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transaction_signatures
    ADD CONSTRAINT uq_tx_signer UNIQUE (transaction_id, signer_type);


--
-- Name: works uq_work_project_code; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.works
    ADD CONSTRAINT uq_work_project_code UNIQUE (project_id, code);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: vehicles vehicles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vehicles
    ADD CONSTRAINT vehicles_pkey PRIMARY KEY (id);


--
-- Name: vehicles vehicles_plate_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vehicles
    ADD CONSTRAINT vehicles_plate_key UNIQUE (plate);


--
-- Name: works works_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.works
    ADD CONSTRAINT works_pkey PRIMARY KEY (id);


--
-- Name: idx_emp_fingerprints_employee; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_emp_fingerprints_employee ON public.employee_fingerprints USING btree (employee_id);


--
-- Name: idx_emp_fingerprints_lookup; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_emp_fingerprints_lookup ON public.employee_fingerprints USING btree (employee_id, finger_position);


--
-- Name: idx_employees_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_employees_user_id ON public.employees USING btree (user_id);


--
-- Name: idx_payroll_entries_employee; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_payroll_entries_employee ON public.payroll_entries USING btree (employee_id);


--
-- Name: idx_payroll_entries_period; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_payroll_entries_period ON public.payroll_entries USING btree (period_id);


--
-- Name: idx_payroll_periods_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_payroll_periods_status ON public.payroll_periods USING btree (status);


--
-- Name: ix_accounting_periods_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_accounting_periods_id ON public.accounting_periods USING btree (id);


--
-- Name: ix_bank_withdrawal_requests_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_bank_withdrawal_requests_id ON public.bank_withdrawal_requests USING btree (id);


--
-- Name: ix_cash_sessions_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cash_sessions_id ON public.cash_sessions USING btree (id);


--
-- Name: ix_signatures_employee_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_signatures_employee_id ON public.transaction_signatures USING btree (employee_id);


--
-- Name: ix_signatures_partner_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_signatures_partner_id ON public.transaction_signatures USING btree (partner_id);


--
-- Name: ix_signatures_supplier_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_signatures_supplier_id ON public.transaction_signatures USING btree (supplier_id);


--
-- Name: ix_system_config_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_system_config_id ON public.system_config USING btree (id);


--
-- Name: ix_transaction_attachments_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_transaction_attachments_id ON public.transaction_attachments USING btree (id);


--
-- Name: ix_transaction_projects_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_transaction_projects_id ON public.transaction_projects USING btree (id);


--
-- Name: ix_transaction_signatures_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_transaction_signatures_id ON public.transaction_signatures USING btree (id);


--
-- Name: ix_transactions_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_transactions_id ON public.transactions USING btree (id);


--
-- Name: ux_floats_one_open_per_employee; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ux_floats_one_open_per_employee ON public.floats USING btree (employee_id) WHERE ((status)::text = ANY ((ARRAY['open'::character varying, 'partial'::character varying])::text[]));


--
-- Name: accounting_periods accounting_periods_closed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.accounting_periods
    ADD CONSTRAINT accounting_periods_closed_by_fkey FOREIGN KEY (closed_by) REFERENCES public.users(id);


--
-- Name: advances_loans advances_loans_creation_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.advances_loans
    ADD CONSTRAINT advances_loans_creation_transaction_id_fkey FOREIGN KEY (creation_transaction_id) REFERENCES public.transactions(id);


--
-- Name: advances_loans advances_loans_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.advances_loans
    ADD CONSTRAINT advances_loans_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id);


--
-- Name: audit_log audit_log_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_log
    ADD CONSTRAINT audit_log_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: bank_withdrawal_requests bank_withdrawal_requests_approved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bank_withdrawal_requests
    ADD CONSTRAINT bank_withdrawal_requests_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES public.users(id);


--
-- Name: bank_withdrawal_requests bank_withdrawal_requests_confirmed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bank_withdrawal_requests
    ADD CONSTRAINT bank_withdrawal_requests_confirmed_by_fkey FOREIGN KEY (confirmed_by) REFERENCES public.users(id);


--
-- Name: bank_withdrawal_requests bank_withdrawal_requests_corporate_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bank_withdrawal_requests
    ADD CONSTRAINT bank_withdrawal_requests_corporate_account_id_fkey FOREIGN KEY (corporate_account_id) REFERENCES public.corporate_accounts(id);


--
-- Name: bank_withdrawal_requests bank_withdrawal_requests_formalized_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bank_withdrawal_requests
    ADD CONSTRAINT bank_withdrawal_requests_formalized_by_fkey FOREIGN KEY (formalized_by) REFERENCES public.users(id);


--
-- Name: bank_withdrawal_requests bank_withdrawal_requests_proposed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bank_withdrawal_requests
    ADD CONSTRAINT bank_withdrawal_requests_proposed_by_fkey FOREIGN KEY (proposed_by) REFERENCES public.users(id);


--
-- Name: bank_withdrawal_requests bank_withdrawal_requests_requested_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bank_withdrawal_requests
    ADD CONSTRAINT bank_withdrawal_requests_requested_by_fkey FOREIGN KEY (requested_by) REFERENCES public.users(id);


--
-- Name: bank_withdrawal_requests bank_withdrawal_requests_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bank_withdrawal_requests
    ADD CONSTRAINT bank_withdrawal_requests_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.cash_sessions(id);


--
-- Name: cash_counts cash_counts_counted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cash_counts
    ADD CONSTRAINT cash_counts_counted_by_fkey FOREIGN KEY (counted_by) REFERENCES public.users(id);


--
-- Name: cash_counts cash_counts_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cash_counts
    ADD CONSTRAINT cash_counts_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.cash_sessions(id);


--
-- Name: cash_sessions cash_sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cash_sessions
    ADD CONSTRAINT cash_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: category_approval_thresholds category_approval_thresholds_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.category_approval_thresholds
    ADD CONSTRAINT category_approval_thresholds_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.transaction_categories(id);


--
-- Name: currency_operations currency_operations_buy_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.currency_operations
    ADD CONSTRAINT currency_operations_buy_transaction_id_fkey FOREIGN KEY (buy_transaction_id) REFERENCES public.transactions(id);


--
-- Name: currency_operations currency_operations_cancelled_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.currency_operations
    ADD CONSTRAINT currency_operations_cancelled_by_user_id_fkey FOREIGN KEY (cancelled_by_user_id) REFERENCES public.users(id);


--
-- Name: currency_operations currency_operations_delivery_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.currency_operations
    ADD CONSTRAINT currency_operations_delivery_transaction_id_fkey FOREIGN KEY (delivery_transaction_id) REFERENCES public.transactions(id);


--
-- Name: employee_fingerprints employee_fingerprints_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_fingerprints
    ADD CONSTRAINT employee_fingerprints_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: employee_fingerprints employee_fingerprints_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_fingerprints
    ADD CONSTRAINT employee_fingerprints_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id) ON DELETE CASCADE;


--
-- Name: employee_salary_history employee_salary_history_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_salary_history
    ADD CONSTRAINT employee_salary_history_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: employee_salary_history employee_salary_history_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_salary_history
    ADD CONSTRAINT employee_salary_history_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id);


--
-- Name: employees employees_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employees
    ADD CONSTRAINT employees_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: expense_approvals expense_approvals_approved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expense_approvals
    ADD CONSTRAINT expense_approvals_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES public.users(id);


--
-- Name: expense_approvals expense_approvals_requested_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expense_approvals
    ADD CONSTRAINT expense_approvals_requested_by_fkey FOREIGN KEY (requested_by) REFERENCES public.users(id);


--
-- Name: expense_approvals expense_approvals_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expense_approvals
    ADD CONSTRAINT expense_approvals_transaction_id_fkey FOREIGN KEY (transaction_id) REFERENCES public.transactions(id);


--
-- Name: float_justifications float_justifications_compensation_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.float_justifications
    ADD CONSTRAINT float_justifications_compensation_transaction_id_fkey FOREIGN KEY (compensation_transaction_id) REFERENCES public.transactions(id);


--
-- Name: float_justifications float_justifications_expense_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.float_justifications
    ADD CONSTRAINT float_justifications_expense_transaction_id_fkey FOREIGN KEY (expense_transaction_id) REFERENCES public.transactions(id);


--
-- Name: float_justifications float_justifications_float_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.float_justifications
    ADD CONSTRAINT float_justifications_float_id_fkey FOREIGN KEY (float_id) REFERENCES public.floats(id) ON DELETE CASCADE;


--
-- Name: float_justifications float_justifications_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.float_justifications
    ADD CONSTRAINT float_justifications_transaction_id_fkey FOREIGN KEY (transaction_id) REFERENCES public.transactions(id);


--
-- Name: floats floats_close_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.floats
    ADD CONSTRAINT floats_close_transaction_id_fkey FOREIGN KEY (close_transaction_id) REFERENCES public.transactions(id);


--
-- Name: floats floats_creation_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.floats
    ADD CONSTRAINT floats_creation_transaction_id_fkey FOREIGN KEY (creation_transaction_id) REFERENCES public.transactions(id);


--
-- Name: floats floats_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.floats
    ADD CONSTRAINT floats_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id);


--
-- Name: import_history import_history_imported_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.import_history
    ADD CONSTRAINT import_history_imported_by_fkey FOREIGN KEY (imported_by) REFERENCES public.users(id);


--
-- Name: import_history import_history_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.import_history
    ADD CONSTRAINT import_history_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.cash_sessions(id);


--
-- Name: installment_payments installment_payments_default_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.installment_payments
    ADD CONSTRAINT installment_payments_default_category_id_fkey FOREIGN KEY (default_category_id) REFERENCES public.transaction_categories(id);


--
-- Name: installment_payments installment_payments_default_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.installment_payments
    ADD CONSTRAINT installment_payments_default_project_id_fkey FOREIGN KEY (default_project_id) REFERENCES public.projects(id);


--
-- Name: installment_payments installment_payments_default_subcategory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.installment_payments
    ADD CONSTRAINT installment_payments_default_subcategory_id_fkey FOREIGN KEY (default_subcategory_id) REFERENCES public.transaction_subcategories(id);


--
-- Name: installment_payments installment_payments_default_work_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.installment_payments
    ADD CONSTRAINT installment_payments_default_work_id_fkey FOREIGN KEY (default_work_id) REFERENCES public.works(id);


--
-- Name: installment_payments installment_payments_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.installment_payments
    ADD CONSTRAINT installment_payments_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id);


--
-- Name: installment_payments installment_payments_supplier_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.installment_payments
    ADD CONSTRAINT installment_payments_supplier_id_fkey FOREIGN KEY (supplier_id) REFERENCES public.suppliers(id);


--
-- Name: installment_records installment_records_installment_payment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.installment_records
    ADD CONSTRAINT installment_records_installment_payment_id_fkey FOREIGN KEY (installment_payment_id) REFERENCES public.installment_payments(id) ON DELETE CASCADE;


--
-- Name: installment_records installment_records_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.installment_records
    ADD CONSTRAINT installment_records_transaction_id_fkey FOREIGN KEY (transaction_id) REFERENCES public.transactions(id);


--
-- Name: money_transfers money_transfers_commission_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.money_transfers
    ADD CONSTRAINT money_transfers_commission_transaction_id_fkey FOREIGN KEY (commission_transaction_id) REFERENCES public.transactions(id);


--
-- Name: money_transfers money_transfers_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.money_transfers
    ADD CONSTRAINT money_transfers_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: money_transfers money_transfers_main_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.money_transfers
    ADD CONSTRAINT money_transfers_main_transaction_id_fkey FOREIGN KEY (main_transaction_id) REFERENCES public.transactions(id);


--
-- Name: partner_account_movements partner_account_movements_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.partner_account_movements
    ADD CONSTRAINT partner_account_movements_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: partner_account_movements partner_account_movements_partner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.partner_account_movements
    ADD CONSTRAINT partner_account_movements_partner_id_fkey FOREIGN KEY (partner_id) REFERENCES public.partners(id);


--
-- Name: partner_account_movements partner_account_movements_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.partner_account_movements
    ADD CONSTRAINT partner_account_movements_transaction_id_fkey FOREIGN KEY (transaction_id) REFERENCES public.transactions(id);


--
-- Name: payroll_entries payroll_entries_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payroll_entries
    ADD CONSTRAINT payroll_entries_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id);


--
-- Name: payroll_entries payroll_entries_liquidated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payroll_entries
    ADD CONSTRAINT payroll_entries_liquidated_by_fkey FOREIGN KEY (liquidated_by) REFERENCES public.users(id);


--
-- Name: payroll_entries payroll_entries_period_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payroll_entries
    ADD CONSTRAINT payroll_entries_period_id_fkey FOREIGN KEY (period_id) REFERENCES public.payroll_periods(id) ON DELETE CASCADE;


--
-- Name: payroll_entries payroll_entries_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payroll_entries
    ADD CONSTRAINT payroll_entries_transaction_id_fkey FOREIGN KEY (transaction_id) REFERENCES public.transactions(id);


--
-- Name: payroll_periods payroll_periods_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payroll_periods
    ADD CONSTRAINT payroll_periods_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: reimbursable_expenses reimbursable_expenses_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reimbursable_expenses
    ADD CONSTRAINT reimbursable_expenses_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.transaction_categories(id);


--
-- Name: reimbursable_expenses reimbursable_expenses_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reimbursable_expenses
    ADD CONSTRAINT reimbursable_expenses_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: reimbursable_expenses reimbursable_expenses_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reimbursable_expenses
    ADD CONSTRAINT reimbursable_expenses_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id);


--
-- Name: reimbursable_expenses reimbursable_expenses_partner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reimbursable_expenses
    ADD CONSTRAINT reimbursable_expenses_partner_id_fkey FOREIGN KEY (partner_id) REFERENCES public.partners(id);


--
-- Name: reimbursable_expenses reimbursable_expenses_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reimbursable_expenses
    ADD CONSTRAINT reimbursable_expenses_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- Name: reimbursable_expenses reimbursable_expenses_subcategory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reimbursable_expenses
    ADD CONSTRAINT reimbursable_expenses_subcategory_id_fkey FOREIGN KEY (subcategory_id) REFERENCES public.transaction_subcategories(id);


--
-- Name: reimbursable_expenses reimbursable_expenses_work_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reimbursable_expenses
    ADD CONSTRAINT reimbursable_expenses_work_id_fkey FOREIGN KEY (work_id) REFERENCES public.works(id);


--
-- Name: retentions_deposits retentions_deposits_creation_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.retentions_deposits
    ADD CONSTRAINT retentions_deposits_creation_transaction_id_fkey FOREIGN KEY (creation_transaction_id) REFERENCES public.transactions(id);


--
-- Name: retentions_deposits retentions_deposits_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.retentions_deposits
    ADD CONSTRAINT retentions_deposits_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id);


--
-- Name: retentions_deposits retentions_deposits_release_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.retentions_deposits
    ADD CONSTRAINT retentions_deposits_release_transaction_id_fkey FOREIGN KEY (release_transaction_id) REFERENCES public.transactions(id);


--
-- Name: retentions_deposits retentions_deposits_supplier_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.retentions_deposits
    ADD CONSTRAINT retentions_deposits_supplier_id_fkey FOREIGN KEY (supplier_id) REFERENCES public.suppliers(id);


--
-- Name: system_config system_config_configured_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_config
    ADD CONSTRAINT system_config_configured_by_fkey FOREIGN KEY (configured_by) REFERENCES public.users(id);


--
-- Name: system_config system_config_last_modified_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_config
    ADD CONSTRAINT system_config_last_modified_by_fkey FOREIGN KEY (last_modified_by) REFERENCES public.users(id);


--
-- Name: transaction_attachments transaction_attachments_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transaction_attachments
    ADD CONSTRAINT transaction_attachments_transaction_id_fkey FOREIGN KEY (transaction_id) REFERENCES public.transactions(id);


--
-- Name: transaction_attachments transaction_attachments_uploaded_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transaction_attachments
    ADD CONSTRAINT transaction_attachments_uploaded_by_fkey FOREIGN KEY (uploaded_by) REFERENCES public.users(id);


--
-- Name: transaction_projects transaction_projects_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transaction_projects
    ADD CONSTRAINT transaction_projects_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- Name: transaction_projects transaction_projects_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transaction_projects
    ADD CONSTRAINT transaction_projects_transaction_id_fkey FOREIGN KEY (transaction_id) REFERENCES public.transactions(id);


--
-- Name: transaction_projects transaction_projects_work_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transaction_projects
    ADD CONSTRAINT transaction_projects_work_id_fkey FOREIGN KEY (work_id) REFERENCES public.works(id);


--
-- Name: transaction_signatures transaction_signatures_captured_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transaction_signatures
    ADD CONSTRAINT transaction_signatures_captured_by_user_id_fkey FOREIGN KEY (captured_by_user_id) REFERENCES public.users(id);


--
-- Name: transaction_signatures transaction_signatures_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transaction_signatures
    ADD CONSTRAINT transaction_signatures_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id);


--
-- Name: transaction_signatures transaction_signatures_partner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transaction_signatures
    ADD CONSTRAINT transaction_signatures_partner_id_fkey FOREIGN KEY (partner_id) REFERENCES public.partners(id);


--
-- Name: transaction_signatures transaction_signatures_signer_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transaction_signatures
    ADD CONSTRAINT transaction_signatures_signer_user_id_fkey FOREIGN KEY (signer_user_id) REFERENCES public.users(id);


--
-- Name: transaction_signatures transaction_signatures_supplier_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transaction_signatures
    ADD CONSTRAINT transaction_signatures_supplier_id_fkey FOREIGN KEY (supplier_id) REFERENCES public.suppliers(id);


--
-- Name: transaction_signatures transaction_signatures_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transaction_signatures
    ADD CONSTRAINT transaction_signatures_transaction_id_fkey FOREIGN KEY (transaction_id) REFERENCES public.transactions(id);


--
-- Name: transaction_subcategories transaction_subcategories_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transaction_subcategories
    ADD CONSTRAINT transaction_subcategories_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.transaction_categories(id);


--
-- Name: transactions transactions_adjustment_ref_period_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_adjustment_ref_period_fkey FOREIGN KEY (adjustment_ref_period) REFERENCES public.accounting_periods(id);


--
-- Name: transactions transactions_approved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES public.users(id);


--
-- Name: transactions transactions_cancel_ref_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_cancel_ref_id_fkey FOREIGN KEY (cancel_ref_id) REFERENCES public.transactions(id);


--
-- Name: transactions transactions_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.transaction_categories(id);


--
-- Name: transactions transactions_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id);


--
-- Name: transactions transactions_partner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_partner_id_fkey FOREIGN KEY (partner_id) REFERENCES public.partners(id);


--
-- Name: transactions transactions_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.cash_sessions(id);


--
-- Name: transactions transactions_subcategory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_subcategory_id_fkey FOREIGN KEY (subcategory_id) REFERENCES public.transaction_subcategories(id);


--
-- Name: transactions transactions_supplier_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_supplier_id_fkey FOREIGN KEY (supplier_id) REFERENCES public.suppliers(id);


--
-- Name: transactions transactions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: transactions transactions_vehicle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_vehicle_id_fkey FOREIGN KEY (vehicle_id) REFERENCES public.vehicles(id);


--
-- Name: vehicles vehicles_usual_driver_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vehicles
    ADD CONSTRAINT vehicles_usual_driver_id_fkey FOREIGN KEY (usual_driver_id) REFERENCES public.employees(id);


--
-- Name: works works_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.works
    ADD CONSTRAINT works_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- PostgreSQL database dump complete
--


