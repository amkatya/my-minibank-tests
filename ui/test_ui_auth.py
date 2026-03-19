"""
UI тесты аутентификации MiniBank
Логин и логаут через пользовательский интерфейс
"""

import pytest

from config.settings import settings, UserRole
from ui.pages.login_page import LoginPage
from ui.pages.dashboard_page import DashboardPage


@pytest.mark.ui
@pytest.mark.auth
class TestUIAuthentication:
    """UI тесты аутентификации"""

    def test_login_with_vip_user(self, driver):
        """Тест логина VIP пользователя"""
        login_page = LoginPage(driver)
        login_page.navigate_to()
        login_page.assert_page_loaded()

        vip_user = settings.get_user(UserRole.VIP_USER)
        login_page.login(vip_user.email, vip_user.password)

        dashboard_page = DashboardPage(driver)
        dashboard_page.assert_page_loaded()

        current_url = driver.current_url
        assert "dashboard" in current_url.lower(), f"VIP user not on dashboard: {current_url}"

    def test_basic_login(self, driver):
        """Тест логина USER пользователя (по заданию 02)"""
        # Переходим на страницу логина
        login_page = LoginPage(driver)
        login_page.navigate_to()

        # Проверяем что страница загрузилась
        login_page.assert_page_loaded()

        # Логинимся как пользователь USER
        test_user = settings.get_user(UserRole.USER)
        login_page.login(test_user.email, test_user.password)

        # Проверяем что попали на dashboard
        dashboard_page = DashboardPage(driver)
        dashboard_page.assert_page_loaded()

    def test_login_logout_flow(self, driver):
        """Тест успешного логаута через UI (по заданию 02)"""
        # Переходим на страницу логина
        login_page = LoginPage(driver)
        login_page.navigate_to()

        # Проверяем что страница загрузилась
        login_page.assert_page_loaded()

        # Логинимся как пользователь USER
        test_user = settings.get_user(UserRole.USER)
        login_page.login(test_user.email, test_user.password)

        # Проверяем что попали на dashboard
        dashboard_page = DashboardPage(driver)
        dashboard_page.assert_page_loaded()

        # Выходим из системы
        dashboard_page.logout()

        # Проверяем что попали на страницу логина
        login_page.assert_page_loaded()

    def test_login_with_wrong_password(self, driver):
        """Негативный тест входа с неправильным паролем (по заданию 02)"""
        # Переходим на страницу логина
        login_page = LoginPage(driver)
        login_page.navigate_to()

        # Проверяем что страница загрузилась
        login_page.assert_page_loaded()

        # Находим пользователя USER
        test_user = settings.get_user(UserRole.USER)

        # Вводим email пользователя USER
        login_page.enter_email(test_user.email)

        # Вводим неправильный пароль пользователя USER
        wrong_password = test_user.password + "1"
        login_page.enter_password(wrong_password)
        login_page.click_submit()

        # Проверяем отображение ошибки
        login_page.assert_error_visible()

        # Проверяем что остались на странице логина
        login_page.assert_page_loaded()