"""
UI тесты счетов
"""

import pytest

from config.settings import settings, UserRole

from ui.pages.login_page import LoginPage
from ui.pages.dashboard_page import DashboardPage
from ui.pages.accounts_page import AccountsPage
from utils.api_client import MiniBankAPIClient
import random
import structlog
import re

logger = structlog.get_logger(__name__)


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
        accounts_page.assert_page_loaded()

        # Проверяем, что есть хотя бы один счёт
        assert accounts_page.find_elements("account_card")

        # Выводим информацию о первой карточке
        cards = accounts_page.get_account_cards()
        logger.info(f"First account card details: {cards[0]}")

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
        accounts_page.assert_page_loaded()

        # Проверяем, что кнопка создания счета ЕСТЬ
        assert accounts_page.find_elements("create_button")

        # Проверяем, что на карточках счетов нет информации о владельце (счета только текущего пользователя)
        assert not accounts_page.owner_block_exists(), "Owner block should not exist but found"

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
        accounts_page.assert_page_loaded()

        # Проверяем, что кнопка создания счета ЕСТЬ
        assert accounts_page.find_elements("create_button")

        # Открываем форму создания счёта
        accounts_page.open_create_form()

        # Проверяем, что можно выбрать владельца счёта и установить баланс
        assert accounts_page.find_elements("user_select")
        assert accounts_page.find_elements("initial_balance_input")

        # Закрываем форму создания счёта
        accounts_page.cancel_create()

    def test_create_basic_account(self, ui_logged_in_admin, api_client, driver):
        """Тест создания счёта CHECKING под ролью ADMIN (с уже залогиненным пользователем)"""
        dashboard_page = ui_logged_in_admin

        # Переходим на страницу My Accounts
        dashboard_page.open_accounts()
        accounts_page = AccountsPage(driver)
        accounts_page.assert_page_loaded()

        # Считаем количество карточек счетов до создания нового счёта
        accounts_page.wait_for_element("account_card", 5)
        quantity_cards_before = len(accounts_page.find_elements("account_card"))

        # Сохраняем текст последней карточки до создания нового счёта
        cards_before = accounts_page.get_account_cards()
        last_card_before = cards_before[0]

        # Получаем user_id
        api_client.login_as_role(UserRole.ADMIN)
        response = api_client.get_users()
        assert response.success, "Failed to get users"
        user_id = response.data["users"][0]["id"]

        # Открываем форму создания счёта и создаём счёт
        accounts_page.open_create_form()
        balance = random.randint(1000, 9999)
        accounts_page.create_account("CHECKING", balance, user_id)

        # Обновляем страницу и переходим в My Accounts
        accounts_page.refresh_page()
        dashboard_page.open_accounts()
        accounts_page.assert_page_loaded()

        # Считаем количество карточек счетов после создания счёта
        accounts_page.wait_for_element("account_card", 5)
        quantity_cards_after = len(accounts_page.find_elements("account_card"))

        # Проверяем, что количество счетов увеличилось на 1
        assert quantity_cards_after - quantity_cards_before == 1

        # Сравниваем содержание последней карточки до и после создания счёта
        cards_after = accounts_page.get_account_cards()
        last_card_after = cards_after[0]
        assert last_card_before != last_card_after

        # Проверяем, что счет создан с правильным типом и балансом
        assert "CHECKING" in last_card_after

        # Проверяем, что счет создан с правильным балансом
        balance_match = re.search(r'\$([\d,]+\.\d{2})', last_card_after)
        assert balance_match, "Баланс не найден в карточке счёта"

        balance_from_card = float(balance_match.group(1).replace(',', ''))

        # Сравниваем с введённым балансом
        assert balance_from_card == float(balance), \
            f"Баланс не совпадает: ожидалось {balance}, получено {balance_from_card}"
