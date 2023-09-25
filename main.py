import argparse
import decimal

from dotenv import dotenv_values
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class OrderTotalCalculator:
    COMPLETED_ORDER_STATUS = "Виконано"

    def __init__(self, email, password, manual_auth=False):
        self.email = email
        self.password = password
        self.manual_auth = manual_auth

        self.driver = webdriver.Chrome()
        self.driver.maximize_window()

        self.total = decimal.Decimal(0)

    def _login(self):
        driver = self.driver

        driver.get("https://rozetka.com.ua/ua/")

        # Wait for page to load
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        if not self.manual_auth:
            # Open Login form
            login_button = driver.find_element(
                by=By.CSS_SELECTOR, value="button.header__button.ng-star-inserted"
            )

            login_button.click()

            # Fill email and password
            email_input = driver.find_element(by=By.ID, value="auth_email")
            email_input.send_keys(self.email)
            password_input = driver.find_element(by=By.ID, value="auth_pass")
            password_input.send_keys(self.password)

            # Click on submit login form button
            submit_login_form_button = driver.find_element(
                by=By.CSS_SELECTOR, value="button.auth-modal__submit"
            )
            submit_login_form_button.click()

        # Wait for user to manually complete login process
        input("Press Enter once you are logged in: ")

    def _parse_price(self, price_str: str) -> decimal.Decimal:
        price_str = price_str.replace(" ", "")
        price_str = price_str.replace("₴", "")
        return decimal.Decimal(price_str)

    def _get_element_or_none(self, by, value):
        try:
            return self.driver.find_element(by=by, value=value)
        except Exception:
            return None

    def _load_page_with_all_orders(self):
        driver = self.driver

        # Open orders page
        driver.get("https://rozetka.com.ua/ua/cabinet/orders/")

        # Wait for orders page to load
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Try to find "Show more" button
        show_more_button_selector = "span.show-more__text"

        show_more_button = self._get_element_or_none(
            by=By.CSS_SELECTOR, value=show_more_button_selector
        )

        while show_more_button:
            show_more_button.click()

            wait.until(EC.url_changes(driver.current_url))

            show_more_button = self._get_element_or_none(
                by=By.CSS_SELECTOR, value=show_more_button_selector
            )

    def _retrieve_orders(self):
        driver = self.driver

        # Retrieve orders
        order_elements = driver.find_elements(By.CSS_SELECTOR, "li.order")
        completed_orders = [
            element
            for element in order_elements
            if self.COMPLETED_ORDER_STATUS
            in element.find_element(
                By.CSS_SELECTOR, "div.order-heading__status > p.order-heading__value"
            ).text
        ]
        money_values = [
            element.find_element(
                By.CSS_SELECTOR, "div.order-heading__price > p.order-heading__value"
            ).text
            for element in completed_orders
        ]

        # Parse money values
        money_values = [self._parse_price(money_value) for money_value in money_values]

        # Calculate total
        self.total = sum(money_values)

    def get_total_spent(self) -> decimal.Decimal:
        self._login()
        self._load_page_with_all_orders()
        self._retrieve_orders()
        return self.total


def main():
    parser = argparse.ArgumentParser(
        description="Script that will print total spent money on Rozetka."
    )
    parser.add_argument("--email", help="Email for login on Rozetka.")
    parser.add_argument("--password", help="Password for login on Rozetka.")
    parser.add_argument(
        "--manual-auth", help="Manually complete login process.", action="store_true"
    )

    args = parser.parse_args()

    env = dotenv_values(".env")

    email = args.email or env.get("EMAIL")
    password = args.password or env.get("PASSWORD")

    if not email or not password:
        print("Please provide email and password for login on Rozetka.")
        return

    total_spent_money = OrderTotalCalculator(
        email=email, password=password, manual_auth=args.manual_auth
    ).get_total_spent()

    print(f"Total spent money on Rozetka: {total_spent_money} ₴")


if __name__ == "__main__":
    main()
