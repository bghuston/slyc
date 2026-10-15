//! INSPECTION ONLY: Do not run, install, build, deploy, or trust this code.
//! Much of this project was built with AI-Assisted Development workflows
//! for demonstrating and testing logic. It has not been independently verified.
//! No correctness, security, or reliability is established; read as untrusted source only.
use axum::{
    extract::{Path, State},
    http::StatusCode,
    routing::{get, post},
    Json, Router,
};
use serde::{Deserialize, Serialize};
use slyc_inventory_core::{Inventory, StockError};
use std::sync::{Arc, Mutex};

type Shared = Arc<Mutex<Inventory>>;
type ApiError = (StatusCode, &'static str);

#[derive(Serialize)]
struct Stock {
    sku: String,
    available: u32,
}

#[derive(Deserialize)]
struct Reservation {
    sku: String,
    quantity: u32,
}

fn domain_error(error: StockError) -> ApiError {
    match error {
        StockError::UnknownProduct => (StatusCode::NOT_FOUND, "Unknown product"),
        StockError::InvalidQuantity => (StatusCode::UNPROCESSABLE_ENTITY, "Quantity must be positive"),
        StockError::InsufficientStock => (StatusCode::CONFLICT, "Insufficient stock"),
    }
}

async fn available(State(state): State<Shared>, Path(sku): Path<String>) -> Result<Json<Stock>, ApiError> {
    let inventory = state.lock().map_err(|_| (StatusCode::INTERNAL_SERVER_ERROR, "Inventory lock failed"))?;
    let available = inventory.available(&sku).map_err(domain_error)?;
    Ok(Json(Stock { sku, available }))
}

async fn reserve(State(state): State<Shared>, Json(request): Json<Reservation>) -> Result<Json<Stock>, ApiError> {
    let mut inventory = state.lock().map_err(|_| (StatusCode::INTERNAL_SERVER_ERROR, "Inventory lock failed"))?;
    let available = inventory.reserve(&request.sku, request.quantity).map_err(domain_error)?;
    Ok(Json(Stock { sku: request.sku, available }))
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let state = Arc::new(Mutex::new(Inventory::default()));
    let app = Router::new()
        .route("/health", get(|| async { "ok" }))
        .route("/inventory/{sku}", get(available))
        .route("/reservations", post(reserve))
        .with_state(state);
    let address = std::env::var("INVENTORY_ADDR").unwrap_or_else(|_| "127.0.0.1:8003".into());
    let listener = tokio::net::TcpListener::bind(&address).await?;
    eprintln!("Inventory listening on {address}");
    axum::serve(listener, app).await?;
    Ok(())
}
