"""
Набор тестов банковских операций:
создание счетов, переводы
"""

import pytest
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from config.settings import UserRole, AccountType
from utils.api_client import MiniBankAPIClient
from ui.pages.login_page import LoginPage
from ui.pages.dashboard_page import DashboardPage
from ui.pages.transfers_page import TransfersPage
from ui.pages.accounts_page import AccountsPage
from decimal import Decimal

import structlog
logger = structlog.get_logger(__name__)


@pytest.mark.api
@pytest.mark.accounts
@pytest.mark.parametrize("role", [
    UserRole.USER,
    UserRole.VIP_USER,
    UserRole.ADMIN,
    UserRole.SUPPORT,
], ids=[
    "USER",
    "VIP",
    "ADMIN",
    "SUPPORT"
])
@pytest.mark.parametrize("account_type", [
    AccountType.SAVINGS,
    AccountType.CHECKING,
], ids=[
    "SAVINGS",
    "CHECKING"
    ])
def test_api_create_accounts_different_roles(driver, api_client, role, account_type):
    """Параметризированный тест создания счёта"""
    # Логинимся под ролью
    login_response = api_client.login_as_role(role)
    assert login_response.success, f"Login failed for {role.value}"

    # Создаём счёт
    user_data = login_response.data["user"]
    account_data = {
        "userId": user_data["id"],
        "accountType": account_type.value,
        "initialBalance": 100.0
    }

    account_response = api_client.create_account(account_data)
    assert account_response.status_code == 201

    account =  account_response.data["account"]

    logger.info(
        "Account created",
        role=role.value,
        account_type=account["account_type"],
        account_id=account["id"],
        account_number=account["account_number"]
    )

    # Логаут
    api_client.logout()

@pytest.mark.ui
@pytest.mark.accounts
@pytest.mark.parametrize("account_type", [
    AccountType.SAVINGS,
    AccountType.CHECKING,
], ids=[
    "SAVINGS",
    "CHECKING"
    ])
def test_create_account_by_user(driver, ui_logged_in_user, api_client, account_type):
    """Параметризированный тест создания счётов SAVINGS и CHECKING под ролью USER и отображения информации о счёте"""
    dashboard_page = ui_logged_in_user

    # Переходим на страницу My Accounts
    dashboard_page.open_accounts()
    accounts_page = AccountsPage(driver)
    accounts_page.assert_page_loaded()

    # Считаем количество карточек счетов до создания нового счёта
    accounts_page.wait_for_element("account_card", 5)
    quantity_cards_before = len(accounts_page.find_elements("account_card"))

    # Сохраняем содержание последней карточки до создания нового счёта
    cards_before = accounts_page.get_account_cards()
    last_card_before = cards_before[0]

    # Открываем форму создания счёта и создаём счёт
    accounts_page.open_create_form()
    accounts_page.create_account(account_type.value)

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

    # Проверяем, что счет создан с правильным типом и нулевым балансом
    assert account_type.value in last_card_after

    balance_from_card = accounts_page.get_balance_from_card(last_card_after)
    assert balance_from_card == 0.0, f"Баланс не совпадает: ожидалось 0.0, получено {balance_from_card}"


@pytest.mark.ui
@pytest.mark.accounts
@pytest.mark.parametrize("account_type", [
    AccountType.SAVINGS,
    AccountType.CHECKING,
], ids=[
    "SAVINGS",
    "CHECKING"
    ])
def test_new_account_visible_in_transfers(driver, ui_logged_in_user, api_client, account_type):
    """Параметризированный тест создания счёта двух типов.
    И проверка отображения счёта в выпадающих списках на странице Transfers.
    Под ролью USER"""
    dashboard_page = ui_logged_in_user

    # Переходим на страницу My Accounts
    dashboard_page.open_accounts()
    accounts_page = AccountsPage(driver)
    accounts_page.assert_page_loaded()

    # Считаем количество карточек счетов до создания нового счёта
    accounts_page.wait_for_element("account_card", 5)
    quantity_cards_before = len(accounts_page.find_elements("account_card"))

    # Открываем форму создания счёта и создаём счёт
    accounts_page.open_create_form()
    accounts_page.create_account(account_type.value)

    # Обновляем страницу и переходим в My Accounts
    accounts_page.refresh_page()
    dashboard_page.open_accounts()
    accounts_page.assert_page_loaded()

    # Считаем количество карточек счетов после создания счёта
    accounts_page.wait_for_element("account_card", 5)
    quantity_cards_after = len(accounts_page.find_elements("account_card"))

    # Проверяем, что количество счетов увеличилось на 1
    assert quantity_cards_after - quantity_cards_before == 1

    # Сохраняем ID созданного счёта (первый в списке)
    account_id = accounts_page.get_account_id(0)

    # Переходим в Transfers
    accounts_page.open_transfers()
    transfers_page = TransfersPage(driver)
    transfers_page.assert_page_loaded()

    # Проверяем наличие счёта в списке From Account
    transfers_page.select_from_account(account_id)

    # Проверяем наличие счёта в списке To Account
    transfers_page.reset_select_from_account()
    transfers_page.select_to_account(account_id)

    # Проверяем наличие счёта на форме To External Account
    transfers_page.click_element("to_external_account_button")
    transfers_page.select_from_account(account_id)


@pytest.mark.ui
@pytest.mark.transfers
def test_external_transfer_checking(driver, make_user_with_account, api_client):
    """Тест перевода между пользователями с CHECKING на CHECKING и проверкой балансов"""
    # Создаём пользователя с не пустым счётом
    sender_data = make_user_with_account(UserRole.USER, 500.0, "CHECKING")
    sender_credentials = sender_data["credentials"]
    sender_account = sender_data["account"]

    # Создаём пользователя с пустым счётом
    recipient_data = make_user_with_account(UserRole.USER, 0.0, "CHECKING")
    recipient_account = recipient_data["account"]

    # Запоминаем балансы счетов до перевода
    response_1 = api_client.get_account_balance(sender_account["id"])
    assert response_1.success, response_1.message
    sender_balance_before = response_1.data["balance"]
    response_2 = api_client.get_account_balance(recipient_account["id"])
    assert response_2.success, response_2.message
    recipient_balance_before = response_2.data["balance"]

    # Вход через UI
    login_page = LoginPage(driver)
    login_page.navigate_to()
    login_page.assert_page_loaded()
    login_page.login(sender_credentials["email"], sender_credentials["password"])

    # Переходим к переводам
    dashboard_page = DashboardPage(driver)
    dashboard_page.assert_page_loaded()
    dashboard_page.open_transfers()

    transfers_page = TransfersPage(driver)
    transfers_page.assert_page_loaded()

    # Выполняем перевод
    transfer_amount = Decimal("111.00")
    description = "Test: Transfer between users CHECKING - CHECKING"

    transfers_page.create_external_transfer(
        from_account=sender_account["id"],
        to_external_account_input=recipient_account["account_number"],
        amount=transfer_amount,
        description=description
    )

    # Проверяем успешность перевода через PageObject (стабильные селекторы)
    transfers_page.assert_success_message()

    # Сохраняем балансы счетов после перевода
    response_3 = api_client.get_account_balance(sender_account["id"])
    assert response_3.success, response_3.message
    sender_balance_after = response_3.data["balance"]
    response_4 = api_client.get_account_balance(recipient_account["id"])
    assert response_4.success, response_4.message
    recipient_balance_after = response_4.data["balance"]

    # Получаем размер комиссии
    response_fee = api_client.get_fee_rules()

    user_fee = response_fee.data["rules"]["external"]["USER"]
    fee = Decimal(str(user_fee))

    # Проверяем, что баланы счетов изменились учитывая комиссию
    assert sender_balance_before - sender_balance_after == transfer_amount + fee
    assert recipient_balance_after - recipient_balance_before == transfer_amount

@pytest.mark.ui
@pytest.mark.transfers
def test_external_transfer_savings_checking(driver, make_user_with_account, api_client):
    """Тест перевода между пользователями с SAVINGS на CHECKING.
    Перевод 500 единиц - верхняя граница дневного лимита + комиссия"""
    # Создаём пользователя с не пустым счётом SAVINGS
    sender_data = make_user_with_account(UserRole.USER, 1000.0, "SAVINGS")
    sender_credentials = sender_data["credentials"]
    sender_account = sender_data["account"]

    # Создаём пользователя с пустым счётом CHECKING
    recipient_data = make_user_with_account(UserRole.USER, 0.0, "CHECKING")
    recipient_account = recipient_data["account"]

    # Запоминаем балансы счетов до перевода
    response_1 = api_client.get_account_balance(sender_account["id"])
    assert response_1.success, response_1.message
    sender_balance_before = response_1.data["balance"]
    response_2 = api_client.get_account_balance(recipient_account["id"])
    assert response_2.success, response_2.message
    recipient_balance_before = response_2.data["balance"]

    # Вход через UI
    login_page = LoginPage(driver)
    login_page.navigate_to()
    login_page.assert_page_loaded()
    login_page.login(sender_credentials["email"], sender_credentials["password"])

    # Переходим к переводам
    dashboard_page = DashboardPage(driver)
    dashboard_page.assert_page_loaded()
    dashboard_page.open_transfers()

    transfers_page = TransfersPage(driver)
    transfers_page.assert_page_loaded()

    # Выполняем перевод
    transfer_amount = Decimal("500.00")
    description = "Test: Transfer between users SAVINGS - CHECKING"

    transfers_page.create_external_transfer(
        from_account=sender_account["id"],
        to_external_account_input=recipient_account["account_number"],
        amount=transfer_amount,
        description=description
    )

    # Проверяем успешность перевода через PageObject (стабильные селекторы)
    transfers_page.assert_success_message()

    # Сохраняем балансы счетов после перевода
    response_3 = api_client.get_account_balance(sender_account["id"])
    assert response_3.success, response_3.message
    sender_balance_after = response_3.data["balance"]
    response_4 = api_client.get_account_balance(recipient_account["id"])
    assert response_4.success, response_4.message
    recipient_balance_after = response_4.data["balance"]

    #Получаем размер комиссии
    response_fee = api_client.get_fee_rules()

    user_fee = response_fee.data["rules"]["external"]["USER"]
    fee = Decimal(str(user_fee))

    # Проверяем, что баланы счетов изменились учитывая комиссию
    assert sender_balance_before - sender_balance_after == transfer_amount + fee
    assert recipient_balance_after - recipient_balance_before == transfer_amount


@pytest.mark.ui
@pytest.mark.transfers
def test_transfer_exceeding_daily_limit(driver, make_user_with_account, api_client):
    """Тест попытки перевода между пользователями с превышением дневного лимита"""
    # Создаём пользователя с не пустым счётом CHECKING
    sender_data = make_user_with_account(UserRole.USER, 1000.0, "CHECKING")
    sender_credentials = sender_data["credentials"]
    sender_account = sender_data["account"]

    # Создаём пользователя с пустым счётом CHECKING
    recipient_data = make_user_with_account(UserRole.USER, 0.0, "CHECKING")
    recipient_account = recipient_data["account"]

    # Запоминаем балансы счетов до перевода
    response_1 = api_client.get_account_balance(sender_account["id"])
    assert response_1.success, response_1.message
    sender_balance_before = response_1.data["balance"]
    response_2 = api_client.get_account_balance(recipient_account["id"])
    assert response_2.success, response_2.message
    recipient_balance_before = response_2.data["balance"]

    # Вход через UI
    login_page = LoginPage(driver)
    login_page.navigate_to()
    login_page.assert_page_loaded()
    login_page.login(sender_credentials["email"], sender_credentials["password"])

    # Переходим к переводам
    dashboard_page = DashboardPage(driver)
    dashboard_page.assert_page_loaded()
    dashboard_page.open_transfers()

    transfers_page = TransfersPage(driver)
    transfers_page.assert_page_loaded()

    # Пытаемся выполнить перевод превышающий дневной лимит
    transfer_amount = Decimal("501.00")
    description = "Test: Transfer between users"

    transfers_page.create_external_transfer(
        from_account=sender_account["id"],
        to_external_account_input=recipient_account["account_number"],
        amount=transfer_amount,
        description=description
    )

    # Проверяем отображаение ошибки
    transfers_page.assert_error_message()

    # Сохраняем балансы счетов после попытки перевода
    response_3 = api_client.get_account_balance(sender_account["id"])
    assert response_3.success, response_3.message
    sender_balance_after = response_3.data["balance"]
    response_4 = api_client.get_account_balance(recipient_account["id"])
    assert response_4.success, response_4.message
    recipient_balance_after = response_4.data["balance"]

    # Проверяем, что баланы счетов не изменились
    assert sender_balance_before - sender_balance_after == 0
    assert recipient_balance_after - recipient_balance_before == 0


@pytest.mark.ui
@pytest.mark.transfers
def test_two_external_transfers(driver, make_user_with_account, api_client):
    """Тест двух внешних переводов подряд."""
    # Создаём пользователя с не пустым счётом SAVINGS
    sender_data = make_user_with_account(UserRole.USER, 10000.0, "SAVINGS")
    sender_credentials = sender_data["credentials"]
    sender_account = sender_data["account"]

    # Создаём пользователя с пустым счётом SAVINGS
    recipient_data = make_user_with_account(UserRole.USER, 0.0, "SAVINGS")
    recipient_account = recipient_data["account"]

    # Запоминаем балансы счетов до перевода
    response_1 = api_client.get_account_balance(sender_account["id"])
    assert response_1.success, response_1.message
    sender_balance_before = response_1.data["balance"]
    response_2 = api_client.get_account_balance(recipient_account["id"])
    assert response_2.success, response_2.message
    recipient_balance_before = response_2.data["balance"]

    # Вход через UI
    login_page = LoginPage(driver)
    login_page.navigate_to()
    login_page.assert_page_loaded()
    login_page.login(sender_credentials["email"], sender_credentials["password"])

    # Переходим к переводам
    dashboard_page = DashboardPage(driver)
    dashboard_page.assert_page_loaded()
    dashboard_page.open_transfers()

    transfers_page = TransfersPage(driver)
    transfers_page.assert_page_loaded()

    # Выполняем первый перевод
    transfer_amount = Decimal("1.00")
    description = "Test: Two external transfers in a row (1)"

    transfers_page.create_external_transfer(
        from_account=sender_account["id"],
        to_external_account_input=recipient_account["account_number"],
        amount=transfer_amount,
        description=description
    )

    # Проверяем успешность перевода через PageObject (стабильные селекторы)
    transfers_page.assert_success_message()

    # Сохраняем балансы счетов после первого перевода
    response_3 = api_client.get_account_balance(sender_account["id"])
    assert response_3.success, response_3.message
    sender_balance_after_first_transfer = response_3.data["balance"]
    response_4 = api_client.get_account_balance(recipient_account["id"])
    assert response_4.success, response_4.message
    recipient_balance_after_first_transfer = response_4.data["balance"]

    # Получаем размер комиссии
    response_fee = api_client.get_fee_rules()

    user_fee = response_fee.data["rules"]["external"]["USER"]
    fee = Decimal(str(user_fee))

    # Проверяем, что баланы счетов изменились учитывая комиссию
    assert sender_balance_before - sender_balance_after_first_transfer == transfer_amount + fee
    assert recipient_balance_after_first_transfer - recipient_balance_before == transfer_amount

    # Выполняем второй перевод
    transfer_amount = Decimal("99.00")
    description = "Test: Two external transfers in a row (2)"

    transfers_page.create_external_transfer(
        from_account=sender_account["id"],
        to_external_account_input=recipient_account["account_number"],
        amount=transfer_amount,
        description=description
    )

    # Проверяем успешность перевода через PageObject (стабильные селекторы)
    transfers_page.assert_success_message()

    # Сохраняем балансы счетов после первого перевода
    response_5 = api_client.get_account_balance(sender_account["id"])
    assert response_5.success, response_5.message
    sender_balance_after_second_transfer = response_5.data["balance"]
    response_6 = api_client.get_account_balance(recipient_account["id"])
    assert response_6.success, response_6.message
    recipient_balance_after_second_transfer = response_6.data["balance"]

    # Получаем размер комиссии
    response_fee = api_client.get_fee_rules()

    user_fee = response_fee.data["rules"]["external"]["USER"]
    fee = Decimal(str(user_fee))

    # Проверяем, что баланы счетов изменились учитывая комиссию
    assert sender_balance_after_first_transfer - sender_balance_after_second_transfer == transfer_amount + fee
    assert recipient_balance_after_second_transfer - recipient_balance_after_first_transfer == transfer_amount
