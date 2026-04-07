from datetime import datetime, date
from pydantic import BaseModel


class CardSale(BaseModel):
    id: str | None = None
    transaction_date: datetime
    card_number: str
    approval_number: str
    approval_amount: int
    vat_amount: int = 0
    tip_amount: int = 0
    acquirer: str
    issuer: str
    transaction_type: str
    status: str
    installment_months: str = "00"
    is_check_card: bool = False
    simple_pay: str = ""
    deposit_date: str = ""
    deposit_amount: int = 0
    fee: int = 0
    store_name: str = ""
    terminal_id: str = ""
    created_at: datetime | None = None


class ScrapeRequest(BaseModel):
    start_date: date
    end_date: date


class ScrapeResponse(BaseModel):
    status: str
    total_count: int
    new_count: int
    message: str


class SalesSummary(BaseModel):
    acquirer: str
    total_amount: int
    count: int
