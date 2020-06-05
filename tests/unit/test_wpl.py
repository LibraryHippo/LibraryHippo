import datetime
import pytest

from app.libraries.wpl import WPL
from app.models import Card, Hold

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
        (
            "The city/the city / China Mi\u00E9ville",
            "The city/the city",
            "China Mi\u00E9ville",
        ),
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


@pytest.mark.parametrize(
    "hold_text,expected_status",
    [
        (" 9 of 83 holds ", (9, 83)),
        ("Ready.", Hold.READY),
        ("IN TRANSIT", Hold.IN_TRANSIT),
        ("CHECK SHELVES", Hold.CHECK_SHELVES),
        ("TRACE", Hold.DELAYED),
    ],
)
def test_check_card_reads_hold_position(hold_text, expected_status, wpl_site):
    wpl_site.post(login_url, text="<a href='/holds'>holds</a>")

    wpl_site.get(
        "/holds",
        text=f"""
             <table class="patFunc">
             <tr class="patFuncHeaders"><th>STATUS</th></tr>
             <tr class="patFuncEntry">
                 <td class="patFuncStatus">{hold_text}</td>
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
    assert hold.status == expected_status


@pytest.mark.parametrize(
    "pickup_text,expected_pickup_location",
    [
        (
            """<div class="patFuncPickupLabel">
                 <label for="locb2677337x00">Pickup Location</label>
               </div>
               <select name="locb2677337x00" id="locb2677337x00">
                 <option value="ww+++">WPL John M. Harper</option>
                 <option value="w++++" selected="selected">WPL Main Library</option>
               </select>""",
            "WPL Main Library",
        ),
        (
            """<div class="patFuncPickupLabel">
                 <label for="locb2677337x00">Pickup Location</label>
               </div>
               <select name="locb2677337x00" id="locb2677337x00">
                 <option value="ww+++">WPL John M. Harper</option>
                 <option value="w++++">WPL Main Library</option>
               </select>""",
            "",
        ),
        ("Pioneer Park", "Pioneer Park"),
    ],
)
def test_check_card_reads_pickup_location(
    pickup_text, expected_pickup_location, wpl_site
):
    wpl_site.post(login_url, text="<a href='/holds'>holds</a>")

    wpl_site.get(
        "/holds",
        text=f"""
<table class="patFunc">
  <tr class="patFuncHeaders"><th>PICKUP LOCATION</th></tr>
  <tr class="patFuncEntry">
    <td class="patFuncPickup">{pickup_text}</td>
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
    assert hold.pickup_location == expected_pickup_location


@pytest.mark.parametrize(
    "frozen_text,expected_is_frozen",
    [
        ('<input type="checkbox" name="freezeb2186875" checked />', True),
        ("&nbps;", False),
    ],
)
def test_check_card_reads_frozen_status(frozen_text, expected_is_frozen, wpl_site):
    wpl_site.post(login_url, text="<a href='/holds'>holds</a>")

    wpl_site.get(
        "/holds",
        text=f"""
<table class="patFunc">
  <tr class="patFuncHeaders">
    <th> FREEZE </th>
  </tr>
  <tr class="patFuncEntry">
    <td  class="patFuncFreeze" align="center">
      {frozen_text}
    </td>
  </tr>
</table>""",
    )

    card = make_card()

    target = WPL()
    check_result = target.check_card(card)

    assert check_result
    assert check_result.holds
    hold = check_result.holds[0]
    if expected_is_frozen:
        assert "frozen" in hold.status_notes
    else:
        assert "frozen" not in hold.status_notes


def test_check_card_reads_hold_expires_date(wpl_site):
    wpl_site.post(login_url, text="<a href='/holds'>holds</a>")

    wpl_site.get(
        "/holds",
        text="""
<table class="patFunc">
  <tr class="patFuncHeaders">
    <th> CANCEL IF NOT FILLED BY </th>
  </tr>
  <tr class="patFuncEntry">
    <td class="patFuncCancel">07-02-21</td>
  </tr>
</table>""",
    )

    card = make_card()

    target = WPL()
    check_result = target.check_card(card)

    assert check_result
    assert check_result.holds
    hold = check_result.holds[0]
    assert hold.expires == datetime.date(2021, 7, 2)


def test_check_card_adds_patron_name_to_holds(wpl_site):
    wpl_site.post(login_url, text="<a href='/holds'>holds</a>")

    wpl_site.get(
        "/holds",
        text="""<table class="patFunc">  <tr class="patFuncEntry"></tr></table>""",
    )

    card = make_card()

    target = WPL()
    check_result = target.check_card(card)

    assert check_result
    assert check_result.holds
    hold = check_result.holds[0]
    assert hold.patron_name == "Blair Conrad"


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
