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
        items_url = urllib.parse.urljoin(
            self.login_url(),
            summary_page.find(name="a", href=re.compile("/items$"))["href"],
        )

        result = "<h1>Holds</h1>"
        for hold in self.get_holds(session, holds_url):
            result += "<dl>"
            for k, v in hold.items():
                result += f"<dt>{k}</dt><dd>{v}</dd>"
            result += "</dl><hr>"

        return result

    def login(self, session, patron, number, pin):
        initial_login_page_view = session.get(self.login_url())
        login_page = BeautifulSoup(initial_login_page_view.text, "html.parser")

        form_fields = self.get_form_fields(login_page)
        form_fields.update({"name": patron, "code": number, "pin": pin})

        login_response = session.post(self.login_url(), form_fields)
        return BeautifulSoup(login_response.text, "html.parser")

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
        holds_page = BeautifulSoup(session.get(holds_url).text, "html.parser")

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
                    # logger.info("cell " + cell_name)
                    hold[cell_name] = "".join(hold_cell.strings)
            holds.append(hold)
        return holds
