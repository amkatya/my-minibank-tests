"""
UI тесты управления пользователями
"""

import pytest

from config.settings import settings, UserRole
from ui.pages.login_page import LoginPage
from ui.pages.dashboard_page import DashboardPage
from ui.pages.users_page import UsersPage
import utils.helpers as helpers

import structlog

logger = structlog.get_logger(__name__)


@pytest.mark.ui
@pytest.mark.users
class TestUIUsers:
    """UI тесты управления пользователями"""

    def test_admin_can_view_users(self, ui_logged_in_admin, api_client, driver):
        """Тест отображания списка пользователей для Admin"""
        # Логинимся как пользователь ADMIN
        dashboard_page = ui_logged_in_admin

        # Переходим на страницу USERS
        dashboard_page.open_users()
        user_page = UsersPage(driver)
        user_page.assert_page_loaded()

        # Проверяем отображение списка пользователей
        assert user_page.is_element_visible("users_table_header")

        # Проверяем, что в списке есть хотя бы один пользователь
        users = user_page.find_elements("users_table_rows")
        assert len(users) > 0

        # Выводим количество пользователей
        logger.info(f"Numbers of users: {len(users)}")

    def test_create_basic_user(self, ui_logged_in_admin, api_client, driver):
        """Тест создания пользователя"""
        # Логинимся как пользователь ADMIN
        dashboard_page = ui_logged_in_admin

        # Переходим на страницу USERS
        dashboard_page.open_users()
        user_page = UsersPage(driver)
        user_page.assert_page_loaded()

        # Запоминаем кол-во пользователей в списке
        users_before = user_page.find_elements("users_table_rows")

        # Генерируем данные пользователя
        user_data = helpers.create_unique_user_data()
        first_name = user_data.get("firstName")
        last_name = user_data.get("lastName")
        email = user_data.get("email")

        # Создаём пользователя
        user_page.create_user(first_name, last_name, email, "USER", "123456")

        # Сообщения о сохранении нет, проверяем, что модальное окно закрылось и отображается страница USERS
        user_page.wait_for_element_invisible("create_form", 5)
        user_page.assert_page_loaded()

        # Перезагружаем страницу, переходим на страницу USERS
        user_page.refresh_page()
        dashboard_page.open_users()
        user_page.assert_page_loaded()

        # Проверяем, что кол-во пользователей увеличилось на 1
        users_after = user_page.find_elements("users_table_rows")
        assert len(users_after) - len(users_before) == 1

        # Проверяем, что отображаются правильные данные
        all_users_data = user_page.get_users_info()
        assert any(user.get('name') == f"{first_name} {last_name}" for user in all_users_data)
        assert any(user.get('email') == email and user.get('role') == "USER" for user in all_users_data)

    def test_user_cannot_manage_users(self, driver):
        """Тест прав пользователя USER на странице USERS"""
        login_page = LoginPage(driver)
        login_page.navigate_to()
        login_page.assert_page_loaded()

        # Логинимся как пользователь USER
        test_user = settings.get_user(UserRole.USER)
        login_page.login(test_user.email, test_user.password)
        dashboard_page = DashboardPage(driver)
        dashboard_page.assert_page_loaded()

        # Проверяем, что кнопки Users нет на странице
        assert not dashboard_page.is_element_visible("//button[contains(text(), 'Users')]")
