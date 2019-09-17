from datetime import datetime, timedelta

from app.commons.context.app_context import AppContext
from app.commons.context.logger import get_logger
from app.commons.context.req_context import build_req_context
from app.commons.jobs.pool import JobPool
from app.payin.core.cart_payment.processor import (
    CartPaymentProcessor,
    CartPaymentInterface,
    LegacyPaymentInterface,
)
from app.payin.core.cart_payment.types import IntentStatus
from app.payin.repository.cart_payment_repo import CartPaymentRepository

logger = get_logger("jobs")


async def job_callback(res, err, ctx):
    if err:  # error handling
        logger.exception("Exception running job")
    else:
        logger.debug("Job successfully completed")


async def capture_uncaptured_payment_intents(
    app_context: AppContext, job_pool: JobPool
):
    """
    Captures all uncaptured payment intents

    :param app_context:
    :param job_pool:
    :return:
    """
    req_context = build_req_context(app_context)

    cart_payment_repo = CartPaymentRepository(app_context)

    cart_payment_interface = CartPaymentInterface(
        app_context, req_context, cart_payment_repo
    )
    legacy_payment_interface = LegacyPaymentInterface(
        app_context, req_context, cart_payment_repo
    )
    cart_payment_processor = CartPaymentProcessor(
        req_context.log, cart_payment_interface, legacy_payment_interface
    )

    uncaptured_payment_intents = cart_payment_repo.find_payment_intents_that_require_capture(
        datetime.utcnow()
    )

    async for payment_intent in uncaptured_payment_intents:
        await job_pool.spawn(
            cart_payment_processor.capture_payment(payment_intent), cb=job_callback
        )


async def resolve_capturing_payment_intents(app_context: AppContext, job_pool: JobPool):
    """
    Payment intents that are in capturing and haven't been updated in a while likely died.
    The capturing process idempotently handles captures, so it should be fine just to re-set
    the state of these payment intents to requires_capture and let the regular cron just try
    to re-capture.

    :return:
    """
    cart_payment_repo = CartPaymentRepository(app_context)

    # Look for payment intents that haven't been updated in an hour and still in capturing
    # This should be a good indication that the capturing process died
    cutoff = datetime.utcnow() - timedelta(hours=1)
    payment_intents = await cart_payment_repo.find_payment_intents_in_capturing(cutoff)

    for payment_intent in payment_intents:
        await job_pool.spawn(
            cart_payment_repo.update_payment_intent_status(
                payment_intent.id,
                new_status=IntentStatus.REQUIRES_CAPTURE.value,
                previous_status=payment_intent.status,
            )
        )