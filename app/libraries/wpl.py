import re
import urllib.parse

from bs4 import BeautifulSoup
from requests import Session

from app.models import CardCheckResult, Checkout, Hold


class WPL:
    __special_hold_statuses = {
        "Ready.": Hold.READY,
        "IN TRANSIT": Hold.IN_TRANSIT,
        "CHECK SHELVES": Hold.CHECK_SHELVES,
        "TRACE": Hold.DELAYED,
    }

    def login_url(self):
        return (
            "https://books.kpl.org/iii/cas/login?service="
            "https://books.kpl.org/patroninfo~S3/"
            "j_acegi_cas_security_check&lang=eng&scope=3"
        )

    def logout_url(self):
        return urllib.parse.urljoin(self.login_url(), "/logout?")

    def item_url(self, original_url):
        return urllib.parse.urljoin(self.login_url(), original_url)

    def check_card(self, card):
        session = Session()
        summary_page = self.login(session, card.patron_name, card.number, card.pin)

        holds_anchor = summary_page.find(name="a", href=re.compile("/holds$"))
        if holds_anchor:
            holds_url = urllib.parse.urljoin(self.login_url(), holds_anchor["href"])
            holds = self.get_holds(session, holds_url)
        else:
            holds = []

        checkouts_anchor = summary_page.find(name="a", href=re.compile("/items$"))
        if checkouts_anchor:
            checkouts_url = urllib.parse.urljoin(
                self.login_url(), checkouts_anchor["href"]
            )
            checkouts = self.get_checkouts(session, checkouts_url)
        else:
            checkouts = []

        self.logout(session)
        return CardCheckResult(holds, checkouts)

    def login(self, session, patron, number, pin):
        initial_login_page_view = session.get(self.login_url())
        login_page = BeautifulSoup(initial_login_page_view.text, "lxml")

        form_fields = self.get_form_fields(login_page)
        form_fields.update({"name": patron, "code": number, "pin": pin})

        login_response = session.post(self.login_url(), form_fields)
        return BeautifulSoup(login_response.text, "lxml")

    def get_form_fields(self, page):
        form_fields = {}
        for input_field in page.find_all("input"):
            if input_field["type"] == "submit":
                form_fields["submit"] = input_field["name"]
            else:
                form_fields[input_field["name"]] = input_field.get("value", "")

        return form_fields

    def get_holds(self, session, holds_url):
        holds = []
        holds_page = BeautifulSoup(session.get(holds_url).text, "lxml")

        holds_table = holds_page.find("table", class_="patFunc")

        for hold_row in holds_table.children:
            if hold_row.name != "tr" or "patFuncEntry" not in hold_row["class"]:
                continue

            hold = Hold()
            for hold_cell in hold_row.children:
                if hold_cell.name != "td":
                    continue
                cell_class = hold_cell["class"][0]
                cell_name = cell_class.replace("patFunc", "")
                try:
                    if cell_name == "Title":
                        text = "".join(hold_cell.strings)
                        parts = text.split(" / ", 1)
                        hold.title = parts[0].strip()
                        if len(parts) > 1:
                            hold.author = parts[1].strip()
                    elif cell_name == "Status":
                        hold.status = self.__parse_hold_status(hold_cell)
                    elif cell_name == "Pickup":
                        hold.pickup = hold_cell.find(
                            "option", selected="selected"
                        ).string
                    elif cell_name == "Freeze" and "checked" in hold_cell.input.attrs:
                        hold.status_notes.append("Frozen")
                    elif cell_name == "Cancel":
                        hold.expires = "".join(hold_cell.strings)
                except:  # noqa there is nothing we can do
                    pass
            holds.append(hold)
        return holds

    def get_checkouts(self, session, checkouts_url):
        checkouts = []
        checkouts_page = BeautifulSoup(session.get(checkouts_url).text, "lxml")

        checkouts_table = checkouts_page.find("table", class_="patFunc")

        for checkout_row in checkouts_table.children:
            if checkout_row.name != "tr":
                continue

            if "patFuncEntry" not in checkout_row["class"]:
                continue
            checkout = Checkout()
            for checkout_cell in checkout_row.children:
                if checkout_cell.name != "td":
                    continue
                cell_class = checkout_cell["class"][0]
                cell_name = cell_class.replace("patFunc", "")
                try:
                    if cell_name == "Title":
                        checkout.title = "".join(checkout_cell.strings)
                    elif cell_name == "Status":
                        checkout.due_date = "".join(checkout_cell.strings)
                except:  # noqa there is nothing we can do
                    pass

            checkouts.append(checkout)
        return checkouts

    def logout(self, session):
        session.get(self.logout_url())

    def __parse_hold_status(self, status_cell):
        text = "".join(status_cell.strings).strip()
        if text in WPL.__special_hold_statuses:
            return WPL.__special_hold_statuses[text]

        parts = text.split()
        if len(parts) > 2 and parts[1] == "of":
            return (int(parts[0]), int(parts[2]))
        return text
