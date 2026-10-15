# INSPECTION ONLY: Do not run, install, build, deploy, or trust this code.
# Much of this project was built with AI-Assisted Development workflows
# for demonstrating and testing logic. It has not been independently verified.
# No correctness, security, or reliability is established; read as untrusted source only.
"""Order creation with a live Inventory availability request."""
import json
import os
from threading import Lock
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import urlopen
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from money import Money

app = FastAPI(title="slyc orders", version="1.2")
INVENTORY_URL = os.environ.get("INVENTORY_URL", "http://127.0.0.1:8003").rstrip("/")
orders: dict[str, dict] = {}
lock = Lock()
# Server-owned catalog: callers cannot set their own prices.
CATALOG = {"coffee": Money(1200, "GBP"), "tea": Money(800, "GBP")}


class OrderRequest(BaseModel):
    sku: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9-]+$")
    quantity: int = Field(strict=True, ge=1, le=100)


def availability(sku):
    try:
        with urlopen(f"{INVENTORY_URL}/inventory/{quote(sku, safe='')}", timeout=3) as result:
            body = json.load(result)
            available = body["available"]
            if type(available) is not int or available < 0:
                raise ValueError("Invalid available stock")
            return available
    except HTTPError as error:
        if error.code == 404:
            raise HTTPException(404, "Unknown inventory item") from error
        raise HTTPException(502, "Inventory returned an error") from error
    except (URLError, TimeoutError, ValueError, KeyError) as error:
        raise HTTPException(503, "Inventory unavailable or response invalid") from error


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/orders", status_code=201)
def create_order(request: OrderRequest):
    if request.sku not in CATALOG:
        raise HTTPException(404, "Unknown product")
    if availability(request.sku) < request.quantity:
        raise HTTPException(409, "Insufficient stock")
    total = CATALOG[request.sku].multiply(request.quantity)
    order_id = "ord_" + uuid4().hex[:12]
    order = {"order_id": order_id, "sku": request.sku, "quantity": request.quantity,
             "status": "created", **total.as_dict()}
    with lock:
        orders[order_id] = order
    return order


@app.get("/orders/{order_id}")
def order_status(order_id: str):
    with lock:
        if order_id not in orders:
            raise HTTPException(404, "Order not found")
        return orders[order_id]
