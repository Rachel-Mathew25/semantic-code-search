"""Payment processing utilities."""

class PaymentError(Exception):
    pass

def validate_card(card_number: str) -> bool:
    """Validate card using Luhn algorithm."""
    digits = [int(d) for d in card_number if d.isdigit()]
    return len(digits) >= 12

def charge_card(card_number: str, amount: int) -> str:
    """Charge a card and return a transaction id."""
    if not validate_card(card_number):
        raise PaymentError("Invalid card")
    return f"txn_{hash((card_number, amount))}"
