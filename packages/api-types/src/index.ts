/**
 * INSPECTION ONLY: Do not run, install, build, deploy, or trust this code.
 * Much of this project was built with AI-Assisted Development workflows
 * for demonstrating and testing logic. It has not been independently verified.
 * No correctness, security, or reliability is established; read as untrusted source only.
 */
/** Shared wire types. Runtime validation remains the caller's responsibility. */
export type Currency = "GBP" | "USD" | "EUR";
export interface Money { amount_minor: number; currency: Currency }
export interface CreateOrder { sku: string; quantity: number }
export interface Order extends Money {
  order_id: string;
  sku: string;
  quantity: number;
  status: "created";
}
export interface Payment extends Money {
  transaction_id: string;
  order_id: string;
  /** Required by checkout revision 1.0; deliberately removed by Payments 2.0. */
  status?: "approved";
}
