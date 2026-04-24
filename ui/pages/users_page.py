"""
Страница пользователей для автотестов MiniBank
Обрабатывает действия по управлению пользователями
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import structlog

from .base_page import BasePage


logger = structlog.get_logger(__name__)


class UsersPage(BasePage):
    """Объект страницы счетов"""
    def __init__(self, driver: webdriver.Remote):
        super().__init__(driver)

        # Селекторы элементов страницы
        self.selectors.update({
            "page_title": 'div:has(button) > h1',
            "create_button": 'h1 + button',
            "create_form": 'h2 + form',
            "first_name_input": 'input[name = "firstName"]',
            "last_name_input": 'input[name = "lastName"]',
            "email_input": 'input[name = "email"]',
            "role_select": 'select[name = "role"]',
            "password_input": 'input[name = "password"]',
            "cancel_create": 'h2 + form button[type="button"]',
            "submit_create": 'h2 + form button[type="submit"]',
            "users_table_header": 'div[style*="grid-template-columns"]:first-of-type',
            "users_table_rows": 'div[style*="grid-template-columns"]:not(:first-of-type)'

        })

    # --------------------------------------------------------------------
    # Реализация абстрактных методов
    # --------------------------------------------------------------------
    def is_loaded(self) -> bool:
        """Проверяет загружена ли страница пользователей"""
        return self.is_element_immediately_visible(self.selectors["page_title"])

    def wait_until_loaded(self) -> None:
        """Ожидает полной загрузки страницы счетов"""
        self.wait_for_element(self.selectors["page_title"])

    def get_page_title(self) -> str:
        return "User Management"

    # --------------------------------------------------------------------
    # Действия на странице
    # --------------------------------------------------------------------
    def open_create_form(self):
        """Открывает форму создания нового пользователя"""
        self.click_element(self.selectors["create_button"])
        self.wait_for_element(self.selectors["create_form"])

    def create_user(self, first_name: str, last_name: str, email: str, role: str, password: str):
        """Создает нового пользователя"""
        self.open_create_form()

        # Заполняем поля
        self.fill_input(self.selectors["first_name_input"], first_name)
        self.fill_input(self.selectors["last_name_input"], last_name)
        self.fill_input(self.selectors["email_input"], email)
        self.select_option(self.selectors["role_select"], role)
        self.fill_input(self.selectors["password_input"], password)

        # Нажимаем "Create User"
        self.click_element(self.selectors["submit_create"])
        self.wait_for_loading_to_complete()

    def get_users_info(self):
        """Получает данные пользователей в списке"""
        rows = self.find_elements(self.selectors["users_table_rows"])
        result = []

        for row in rows:
            cells = row.find_elements(By.CSS_SELECTOR, ":scope > div")

            user_data = {
                "name": cells[0].text,
                "email": cells[1].text,
                "role": cells[2].text,
                "status": cells[3].text
            }

            result.append(user_data)

        return result

    # --------------------------------------------------------------------
    # Проверки состояния
    # --------------------------------------------------------------------
    def wait_for_element_invisible(self, selector, timeout=10):
        """Ожидает, пока элемент станет невидимым"""
        element = self.find_element(selector)
        WebDriverWait(self.driver, timeout).until(
            EC.invisibility_of_element(element)
        )
        assert not self.is_element_visible(selector), f"Element {selector} is visible"

