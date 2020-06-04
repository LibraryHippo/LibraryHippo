import pytest

from app.libraries.wpl import WPL
from app.models import Card

login_url = (
    "https://books.kpl.org/iii/cas/login?service="
    + "https://books.kpl.org/patroninfo~S3/"
    + "j_acegi_cas_security_check&lang=eng&scope=3"
)

logout_url = "https://books.kpl.org/logout"


@pytest.mark.parametrize(
    "title_text,expected_title,expected_author",
    [
        (
            "Full throttle : stories / Joe Hill / Someone Else",
            "Full throttle : stories",
            "Joe Hill / Someone Else",
        ),
        ("Full throttle : stories / Joe Hill", "Full throttle : stories", "Joe Hill",),
        ("Full throttle : stories", "Full throttle : stories", "",),
    ],
)
def test_check_card_slashes_in_holds_titles_split_right(
    title_text, expected_title, expected_author, wpl_site
):
    wpl_site.post(login_url, text="<a href='/holds'>holds</a>")

    wpl_site.get(
        "/holds",
        text=f"""
<table class="patFunc">
  <tr class="patFuncHeaders"><th>TITLE</th></tr>
  <tr class="patFuncEntry">
    <td class="patFuncTitle">
      <label for="cancelb2692795x05">
        <a href="https://URL"target="_parent">
          <span class="patFuncTitleMain">{title_text}</span>
        </a>
      </label>
    <br>
    </td>
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
    assert hold.title == expected_title
    assert hold.author == expected_author


def test_check_card_reads_numeric_hold_position_as_tuple(wpl_site):
    wpl_site.post(login_url, text="<a href='/holds'>holds</a>")

    wpl_site.get(
        "/holds",
        text="""
             <table class="patFunc">
             <tr class="patFuncHeaders"><th>STATUS</th></tr>
             <tr class="patFuncEntry">
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
    assert hold.status == (9, 83)


def test_check_card_logs_out_after_check(wpl_site):
    card = make_card()

    target = WPL()
    target.check_card(card)

    assert wpl_site.last_request.method == "GET"
    assert wpl_site.last_request.url == logout_url


def make_card():
    card = Card()
    card.patron_name = "Blair Conrad"
    card.number = "123456789"
    card.pin = "9876"
    return card


@pytest.fixture
def wpl_site(requests_mock):
    """
    A requests-mock object that has reasonable defaults for simulating the WPL website
    """
    requests_mock.get(login_url, text="")
    requests_mock.post(login_url, text="")
    requests_mock.get(logout_url, text="")
    return requests_mock
