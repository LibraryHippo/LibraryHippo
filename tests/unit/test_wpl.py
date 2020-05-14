from app.libraries.wpl import WPL
from app.models import Card


def test_check_card_finds_holds():
    card = make_card()

    target = WPL()
    check_result = target.check_card(card)

    assert check_result is not None
    assert check_result["holds"]


def make_card():
    card = Card()
    card.patron_name = "Blair Conrad"
    card.number = "123456789"
    card.pin = "9876"
    return card
