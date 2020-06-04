from app.libraries.wpl import WPL
from app.models import Card


def test_check_card_finds_holds(requests_mock):
    login_url = (
        "https://books.kpl.org/iii/cas/login?service="
        + "https://books.kpl.org/patroninfo~S3/"
        + "j_acegi_cas_security_check&lang=eng&scope=3"
    )

    requests_mock.get(login_url, text="")
    requests_mock.post(login_url, text="<a href='/holds'>holds</a>")

    requests_mock.get(
        "/holds",
        text="""
             <table class="patFunc">
             <tr class="patFuncHeaders"><th> TITLE </th><th>STATUS</th></tr>
             <tr class="patFuncEntry">
                 <td class="patFuncTitle">Blood heir / Amélie Wen Zhao</td>
                 <td class="patFuncStatus"> 9 of 83 holds </td>
             </tr>
             </table>
             """,
    )

    card = make_card()

    target = WPL()
    check_result = target.check_card(card)

    assert check_result
    assert check_result.holds
    hold = check_result.holds[0]
    assert hold.title == "Blood heir / Amélie Wen Zhao"
    assert hold.status == " 9 of 83 holds "


def make_card():
    card = Card()
    card.patron_name = "Blair Conrad"
    card.number = "123456789"
    card.pin = "9876"
    return card
