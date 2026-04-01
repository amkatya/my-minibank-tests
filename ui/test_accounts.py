"""
UI тесты счетов
"""

import pytest

import random

from config.settings import settings, UserRole

from ui.pages.login_page import LoginPage
from ui.pages.dashboard_page import DashboardPage
from ui.pages.accounts_page import AccountsPage


@pytest.mark.ui
@pytest.mark.accounts
class TestUIAccounts:
    """UI тесты счетов"""

    def test_view_user_accounts(self, driver):
        """Тест просмотра информации о счете пользователя"""
        # Переходим на страницу логина
        login_page = LoginPage(driver)
        login_page.navigate_to()
        login_page.assert_page_loaded()

        # Логинимся как пользователь USER
        test_user = settings.get_user(UserRole.USER)
        login_page.login(test_user.email, test_user.password)
        dashboard_page = DashboardPage(driver)
        dashboard_page.assert_page_loaded()

        # Переходим на страницу My Accounts
        dashboard_page.open_accounts()
        accounts_page = AccountsPage(driver)
        accounts_page.is_loaded()

        # Проверяем, что есть хотя бы один счёт
        assert accounts_page.is_element_visible("account_card")

        # Выводим информацию о первой карточке
        cards = accounts_page.get_account_cards()
        print(cards[0])

    def test_user_account_permissions(self, driver):
        """Тест прав пользователя USER на странице My Accounts"""
        login_page = LoginPage(driver)
        login_page.navigate_to()
        login_page.assert_page_loaded()

        # Логинимся как пользователь USER
        test_user = settings.get_user(UserRole.USER)
        login_page.login(test_user.email, test_user.password)
        dashboard_page = DashboardPage(driver)
        dashboard_page.assert_page_loaded()

        # Переходим на страницу My Accounts
        dashboard_page.open_accounts()
        accounts_page = AccountsPage(driver)
        accounts_page.is_loaded()

        # Проверяем, что кнопка создания счета ЕСТЬ
        assert accounts_page.is_element_visible("create_button")

        # Проверяем, что на карточках счетов нет информации о владельце (счета только текущего пользователя)
        assert not accounts_page.find_elements("owner_account")

        # Открываем форму создания счёта
        accounts_page.open_create_form()

        # Проверяем, что нет возможности выбрать владельца счёта и установить баланс
        assert not accounts_page.find_elements("user_select")
        assert not accounts_page.find_elements("initial_balance_input")

    def test_admin_account_permissions(self, driver):
        """Тест прав пользователя ADMIN на странице My Accounts"""
        login_page = LoginPage(driver)
        login_page.navigate_to()
        login_page.assert_page_loaded()

        # Логинимся как пользователь ADMIN
        test_user = settings.get_user(UserRole.ADMIN)
        login_page.login(test_user.email, test_user.password)
        dashboard_page = DashboardPage(driver)
        dashboard_page.assert_page_loaded()

        # Переходим на страницу My Accounts
        dashboard_page.open_accounts()
        accounts_page = AccountsPage(driver)
        accounts_page.is_loaded()

        # Проверяем, что кнопка создания счета ЕСТЬ
        assert accounts_page.is_element_visible("create_button")

        # Открываем форму создания счёта
        accounts_page.open_create_form()

        # Проверяем, что можно выбрать владельца счёта и установить баланс
        assert accounts_page.is_element_visible("user_select")
        assert accounts_page.is_element_visible("initial_balance_input")

        # Закрываем форму создания счёта
        accounts_page.cancel_create()

    def test_create_basic_account(self, ui_logged_in_admin, driver):
        """Тест создания счёта под ролью ADMIN (с уже залогиненным пользователем)"""
        dashboard_page = ui_logged_in_admin

        # Переходим на страницу My Accounts
        dashboard_page.open_accounts()
        accounts_page = AccountsPage(ui_logged_in_admin.driver)
        accounts_page.is_loaded()

        # Считаем количество карточек счетов до создания нового счёта
        accounts_page.wait_for_element("account_card", 5)
        quantity_cards_before = len(accounts_page.find_elements("account_card"))

        # Сохраняем текст последней карточки до создания нового счёта
        cards_before = accounts_page.get_account_cards()
        last_card_before = cards_before[0]

        # Открываем форму создания счёта и создаём счёт
        accounts_page.open_create_form()
        balance = random.randint(1000, 9999)
        accounts_page.create_account("CHECKING", balance, "32181b39-af7b-4c4f-b4e0-40c02f9b8b7c")

        # Обновляем страницу и переходим в My Accounts
        accounts_page.refresh_page()
        dashboard_page.open_accounts()
        accounts_page.is_loaded()

        # Считаем количество карточек счетов после создания счёта
        accounts_page.wait_for_element("account_card", 5)
        quantity_cards_after = len(accounts_page.find_elements("account_card"))

        # Проверяем, что количество счетов увеличилось на 1
        assert quantity_cards_after - quantity_cards_before == 1

        # Сравниваем текст последней карточки до и после создания счёта
        cards_after = accounts_page.get_account_cards()
        last_card_after = cards_after[0]
        assert last_card_before != last_card_after
