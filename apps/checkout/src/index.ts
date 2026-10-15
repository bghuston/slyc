/**
 * INSPECTION ONLY: Do not run, install, build, deploy, or trust this code.
 * Much of this project was built with AI-Assisted Development workflows
 * for demonstrating and testing logic. It has not been independently verified.
 * No correctness, security, or reliability is established; read as untrusted source only.
 */
import { randomUUID } from "node:crypto";
import type { Order, Payment } from "@slyc/api-types";

const orders = process.env.ORDERS_URL ?? "http://127.0.0.1:8001";
const payments = process.env.PAYMENTS_URL ?? "http://127.0.0.1:8002";
const revision = process.env.CHECKOUT_CONTRACT_REVISION ?? "1.0";

async function request<T>(url: string, body?: unknown, key?: string): Promise<T> {
  const response = await fetch(url, {
    method: body === undefined ? "GET" : "POST",
    headers: { "Content-Type": "application/json", ...(key ? { "Idempotency-Key": key } : {}) },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    signal: AbortSignal.timeout(5000),
  });
  if (!response.ok) throw new Error(`${url}: HTTP ${response.status}: ${await response.text()}`);
  return await response.json() as T;
}

async function checkout(): Promise<void> {
  if (!["1.0", "1.1"].includes(revision)) throw new Error("CHECKOUT_CONTRACT_REVISION must be 1.0 or 1.1");
  const quantity = Number(process.argv[3] ?? "1");
  if (!Number.isInteger(quantity) || quantity < 1 || quantity > 100) throw new Error("Quantity must be an integer from 1 to 100");
  const order = await request<Order>(`${orders}/orders`, { sku: process.argv[2] ?? "coffee", quantity });
  if (!order || typeof order.order_id !== "string" || !Number.isSafeInteger(order.amount_minor) ||
      order.amount_minor <= 0 || !["GBP", "USD", "EUR"].includes(order.currency)) {
    throw new Error("Invalid order response");
  }
  const payment = await request<Payment>(`${payments}/payments`, {
    order_id: order.order_id, amount_minor: order.amount_minor, currency: order.currency,
  }, randomUUID());
  if (!payment || typeof payment.transaction_id !== "string") throw new Error("Missing transaction_id");
  if (revision === "1.0" && payment.status !== "approved") throw new Error("Contract 1.0 requires approved payment status");
  const status = await request<Order>(`${orders}/orders/${encodeURIComponent(order.order_id)}`);
  console.log(JSON.stringify({ order: status, payment, consumer_contract: revision }, null, 2));
}

checkout().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
