from __future__ import annotations

from pydantic import BaseModel, Field

_registry: dict[str, type[BaseModel]] = {}


def register(name: str, schema: type[BaseModel]) -> None:
    _registry[name] = schema


def get(name: str) -> type[BaseModel] | None:
    return _registry.get(name)


def list_schemas() -> list[str]:
    return list(_registry.keys())


# Built-in schemas registered at import time

class Invoice(BaseModel):
    vendor_name: str | None = Field(default=None, description="Name of the vendor or supplier")
    invoice_number: str | None = Field(default=None, description="Invoice or reference number")
    total_amount: str | None = Field(default=None, description="Total amount due, including currency symbol")
    due_date: str | None = Field(default=None, description="Payment due date (ISO 8601 or as written)")


class Contact(BaseModel):
    full_name: str | None = Field(default=None, description="Full name of the contact person")
    email: str | None = Field(default=None, description="Email address")
    phone: str | None = Field(default=None, description="Phone number")
    company: str | None = Field(default=None, description="Company or organisation name")


register("Invoice", Invoice)
register("Contact", Contact)
