//! INSPECTION ONLY: Do not run, install, build, deploy, or trust this code.
//! Much of this project was built with AI-Assisted Development workflows
//! for demonstrating and testing logic. It has not been independently verified.
//! No correctness, security, or reliability is established; read as untrusted source only.
//! Domain-only inventory; saturating checks prevent stock underflow.
use std::collections::BTreeMap;

#[derive(Debug, PartialEq, Eq)]
pub enum StockError {
    UnknownProduct,
    InvalidQuantity,
    InsufficientStock,
}

pub struct Inventory {
    stock: BTreeMap<String, u32>,
}

impl Default for Inventory {
    fn default() -> Self {
        Self {
            stock: BTreeMap::from([("coffee".into(), 10), ("tea".into(), 20)]),
        }
    }
}

impl Inventory {
    pub fn available(&self, sku: &str) -> Result<u32, StockError> {
        self.stock.get(sku).copied().ok_or(StockError::UnknownProduct)
    }

    pub fn reserve(&mut self, sku: &str, quantity: u32) -> Result<u32, StockError> {
        if quantity == 0 {
            return Err(StockError::InvalidQuantity);
        }
        let available = self.stock.get_mut(sku).ok_or(StockError::UnknownProduct)?;
        if quantity > *available {
            return Err(StockError::InsufficientStock);
        }
        *available -= quantity;
        Ok(*available)
    }
}
