# INSPECTION ONLY: Do not run, install, build, deploy, or trust this code.
# Much of this project was built with AI-Assisted Development workflows
# for demonstrating and testing logic. It has not been independently verified.
# No correctness, security, or reliability is established; read as untrusted source only.
"""Simulated payments. Memory only; no payment gateway or credentials."""
import os
from threading import Lock
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from money import Money

app = FastAPI(title="slyc payments", version="1.1")
revision = os.environ.get("PAYMENTS_API_REVISION", "1")
if revision not in {"1", "2"}:
    raise ValueError("PAYMENTS_API_REVISION must be 1 or 2")
transactions: dict[str, dict] = {}
idempotency: dict[str, tuple[dict, str]] = {}
lock = Lock()


class PaymentRequest(BaseModel):
    order_id: str = Field(min_length=1, max_length=128)
    amount_minor: int = Field(strict=True, gt=0, le=1_000_000)
    currency: str = "GBP"


def response(transaction):
    # Revision 2 deliberately breaks checkout contract revision 1.0.
    return {key: value for key, value in transaction.items() if revision != "2" or key != "status"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/payments", status_code=201)
def create_payment(request: PaymentRequest, idempotency_key: str = Header(min_length=1, max_length=128)):
    try:
        money = Money(request.amount_minor, request.currency)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    payload = request.model_dump()
    with lock:
        if idempotency_key in idempotency:
            previous, transaction_id = idempotency[idempotency_key]
            if previous != payload:
                raise HTTPException(409, "Idempotency key reused with a different request")
            return response(transactions[transaction_id])
        transaction_id = "txn_" + uuid4().hex[:12]
        transaction = {"transaction_id": transaction_id, "order_id": request.order_id,
                       "status": "approved", **money.as_dict()}
        transactions[transaction_id] = transaction
        idempotency[idempotency_key] = (payload, transaction_id)
        return response(transaction)


@app.get("/payments/{transaction_id}")
def payment_status(transaction_id: str):
    with lock:
        if transaction_id not in transactions:
            raise HTTPException(404, "Payment not found")
        return response(transactions[transaction_id])
