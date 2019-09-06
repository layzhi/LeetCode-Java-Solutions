import pydantic
from typing import Optional

from pydantic import Json

from app.commons.api.models import PaymentRequest, PaymentResponse
from app.commons.types import CountryCode, CurrencyType
from app.payout.types import (
    PayoutAccountId,
    PayoutAccountToken,
    PayoutMethodId,
    PayoutMethodToken,
    PayoutAccountTargetType,
    PayoutAccountTargetId,
    StripeManagedAccountId,
    StripeFileHandle,
    PayoutAmountType,
    PayoutType,
    PayoutMethodType,
    PayoutTargetType,
)

__all__ = ["PayoutAccountId", "PayoutAccountToken"]


class CreatePayoutAccount(PaymentRequest):
    target_id: PayoutAccountTargetId
    target_type: PayoutAccountTargetType
    country: CountryCode
    currency: CurrencyType


class PayoutAccount(PaymentResponse):
    id: PayoutAccountId
    stripe_managed_account_id: StripeManagedAccountId
    statement_descriptor: str
    verification_requirements: Json
    # todo: add payout_methods, payout_schedule


class VerificationDetails(PaymentRequest):
    class DateOfBirth(pydantic.BaseModel):
        day: int
        month: int
        year: int

    class Address(pydantic.BaseModel):
        country: CountryCode
        state: str
        city: str
        line1: str
        line2: str
        postal_code: str

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[DateOfBirth] = None
    business_name: Optional[str] = None
    business_tax_id: Optional[str] = None
    address: Optional[Address] = None
    id_file: Optional[StripeFileHandle] = None
    personal_identification_number: Optional[str] = None
    ssn_last_four: Optional[str] = None
    # we need pass in country and currency to create stripe account unless payment account table can store them
    country: Optional[CountryCode] = None
    currency: Optional[CurrencyType] = None
    ...


class CreatePayoutMethod(PaymentRequest):
    token: PayoutMethodToken


class PayoutMethod(PaymentResponse):
    """
    Bank or Debit Card
    """

    id: PayoutMethodId
    ...


class PayoutRequest(PaymentRequest):
    amount: PayoutAmountType
    payout_type: PayoutType = PayoutType.Standard
    target_id: Optional[str] = None
    target_type: Optional[PayoutTargetType] = None
    transfer_id: Optional[str] = None
    payout_id: Optional[str] = None
    method: Optional[PayoutMethodType]
    submitted_by: Optional[str] = None


class Payout(PaymentResponse):
    pass
