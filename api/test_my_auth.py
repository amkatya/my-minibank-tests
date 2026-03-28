import pytest

from config.settings import settings, UserRole
from utils.api_client import MiniBankAPIClient, APIResponse


@pytest.mark.api
@pytest.mark.auth
class TestMyAuthAPI:

    def test_my_first_api_login(self, api_client: MiniBankAPIClient):
        """Мой первый API тест логина"""
        # Получаем данные пользователя USER
        test_user = settings.get_user(UserRole.USER)

        # Логинимся
        response = api_client.login(test_user.email, test_user.password)

        # Проверяем удачный вход, статус 200
        assert response.success
        assert response.status_code == 200

        # Проверяем наличие токена
        assert 'token' in response.data, "Token missing in response"
        token = response.data['token']
        assert isinstance(token, str), "Token should be string"
        assert len(token) > 0, 'Token should not be empty'

        # Проверяем наличие пользователя и соответсвие email и роли
        assert 'user' in response.data, "User missing in response"
        user_info = response.data['user']
        assert user_info['email'] == test_user.email
        assert user_info['role'] == test_user.role.value

    def test_already_logged_in_user(self, logged_in_user, api_client: MiniBankAPIClient):
        """Тест с уже залогиненным пользователем"""
        # Получаем данные пользователя USER
        test_user = settings.get_user(UserRole.USER)

        # Проверяем удачный вход
        assert logged_in_user['email'] == test_user.email
        assert logged_in_user['role'] == test_user.role.value

    def test_token_validation(self, logged_in_user, api_client: MiniBankAPIClient):
        """Тест валидации токена"""
        # Проверяем валидность токена
        validation_response = api_client.validate_token()
        assert validation_response.success
        assert validation_response.status_code == 200

    @pytest.mark.parametrize("role", [
        UserRole.USER,
        UserRole.VIP_USER,
        UserRole.ADMIN,
        UserRole.SUPPORT
    ], ids=[
        "user",
        "vip",
        "admin",
        "support"
    ])
    def test_login_different_roles(self, api_client, role):
        """Тест логина разных ролей через параметризацию"""
        # Получаем данные пользователей
        test_user = settings.get_user(role)

        # Логинимся
        response = api_client.login(test_user.email, test_user.password)

        # Проверяем удачный вход, статус 200
        assert response.success
        assert response.status_code == 200

        # Проверяем наличие пользователя и соответсвие роли
        assert 'user' in response.data, "User missing in response"
        user_info = response.data['user']
        assert user_info['role'] == test_user.role.value

    @pytest.mark.parametrize("email, password, expected_status", [
        (settings.get_user(UserRole.USER).email, "wrong_password", [400, 401, 403]),
        ("fake@nomail.ru", settings.get_user(UserRole.USER).password, [400, 401, 403]),
        ("", settings.get_user(UserRole.USER).password, [400, 401, 403]),
        (settings.get_user(UserRole.USER).email, "", [400, 401, 403])
    ], ids=[
        "Wrong password",
        "Wrong email",
        "Empty email",
        "Empty password"
    ])
    def test_login_errors(self, api_client, email, password, expected_status):
        """Параметризированный тест ошибок логина"""
        # Логинимся
        response = api_client.login(email, password)
        # Проверяем, что вход не удался
        assert not response.success
        assert response.status_code in expected_status

        # Проверяем отсутсвие токена
        assert 'token' not in response.data
