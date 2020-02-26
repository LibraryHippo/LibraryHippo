import re
import urllib.parse

from bs4 import BeautifulSoup
from requests import Session


class WPL:
    def login_url(self):
        return (
            "https://books.kpl.org/iii/cas/login?service="
            + "https://books.kpl.org/patroninfo~S3/j_acegi_cas_security_check&lang=eng&scope=3"
        )

    def logout_url(self):
        return urllib.parse.urljoin(self.login_url(), "/logout?")

    def item_url(self, original_url):
        return urllib.parse.urljoin(self.login_url(), original_url)

    def check_card(self, patron, number, pin):
        session = Session()
        summary_page = self.login(session, patron, number, pin)

        holds_url = urllib.parse.urljoin(
            self.login_url(),
            summary_page.find(name="a", href=re.compile("/holds$"))["href"],
        )
        checkouts_url = urllib.parse.urljoin(
            self.login_url(),
            summary_page.find(name="a", href=re.compile("/items$"))["href"],
        )

        holds = self.get_holds(session, holds_url)
        checkouts = self.get_checkouts(session, checkouts_url)

        return {
            "holds": holds,
            "checkouts": checkouts,
        }

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

            hold = {}
            for hold_cell in hold_row.children:
                if hold_cell.name != "td":
                    continue
                cell_class = hold_cell["class"][0]
                cell_name = cell_class.replace("patFunc", "")
                if cell_name == "Mark":
                    continue
                if cell_name == "Pickup":
                    hold[cell_name] = hold_cell.find(
                        "option", selected="selected"
                    ).string
                elif cell_name == "Freeze":
                    hold[cell_name] = "checked" in hold_cell.input.attrs
                else:
                    hold[cell_name] = "".join(hold_cell.strings)
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
            checkout = {}
            for checkout_cell in checkout_row.children:
                if checkout_cell.name != "td":
                    continue
                cell_class = checkout_cell["class"][0]
                cell_name = cell_class.replace("patFunc", "")
                if cell_name == "Mark":
                    continue
                else:
                    checkout[cell_name] = "".join(checkout_cell.strings)
            checkouts.append(checkout)
        return checkouts
