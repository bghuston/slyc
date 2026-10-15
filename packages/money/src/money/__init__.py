# INSPECTION ONLY: Do not run, install, build, deploy, or trust this code.
# Much of this project was built with AI-Assisted Development workflows
# for demonstrating and testing logic. It has not been independently verified.
# No correctness, security, or reliability is established; read as untrusted source only.
"""Exact minor-unit arithmetic: no binary floats or currency conversion."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Money:
    amount_minor: int
    currency: str = "GBP"

    def __post_init__(self):
        if type(self.amount_minor) is not int or self.amount_minor < 0:
            raise ValueError("amount_minor must be a nonnegative integer")
        if self.currency not in {"GBP", "USD", "EUR"}:
            raise ValueError("Supported demo currencies: GBP, USD, EUR")

    def __add__(self, other):
        if not isinstance(other, Money):
            return NotImplemented
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount_minor + other.amount_minor, self.currency)

    def multiply(self, quantity: int):
        if type(quantity) is not int or quantity < 0:
            raise ValueError("quantity must be a nonnegative integer")
        return Money(self.amount_minor * quantity, self.currency)

    def as_dict(self):
        return {"amount_minor": self.amount_minor, "currency": self.currency}
