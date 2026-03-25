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
        assert response.success is True
        assert response.status_code == 200

        # Проверяем наличие токена
        if 'token' in response.data:
            token = response.data['token']
            assert isinstance(token, str), "Token should be string"
            assert len(token) > 0, 'Token should not be empty'

        # Проверяем наличие пользователя и соответсвие email и роли
        if 'user' in response.data:
            user_info = response.data['user']
            assert user_info['email'] == test_user.email
            assert user_info['role'] == test_user.role.value

        print(response.data)

    def test_login_wrong_password(self, api_client: MiniBankAPIClient):
        """ Негативный API тест логина c неправильным паролем"""
        # Получаем данные пользователя USER
        test_user = settings.get_user(UserRole.USER)

        # Вводим правильный email и неправильный пароль
        response = api_client.login(test_user.email, test_user.password + "1")

        # Проверяем, что вход не удался
        assert response.success == False
        assert response.status_code in [400, 401, 403]

        # Проверяем отсутсвие токена
        assert 'token' not in response.data

    def test_login_empty_email(self, api_client: MiniBankAPIClient):
        """ Негативный API тест логина c пустым email"""
        # Получаем данные пользователя USER
        test_user = settings.get_user(UserRole.USER)

        # Вводим пустой email и правильный пароль
        response = api_client.login("", test_user.password)

        # Проверяем, что вход не удался
        assert response.success == False
        assert response.status_code in [400, 401, 403]

        # Проверяем отсутсвие токена
        assert 'token' not in response.data

    def test_login_empty_password(self, api_client: MiniBankAPIClient):
        """ Негативный API тест логина c пустым паролем"""
        # Получаем данные пользователя USER
        test_user = settings.get_user(UserRole.USER)

        # Вводим правильный email и не вводим пароль
        response = api_client.login(test_user.email, "")

        # Проверяем, что вход не удался
        assert response.success is False
        assert response.status_code in [400, 401, 403]

        # Проверяем отсутсвие токена
        assert 'token' not in response.data

    def test_login_wrong_email(self, api_client: MiniBankAPIClient):
        """ Негативный API тест логина c несуществующим email"""
        # Получаем данные пользователя USER
        test_user = settings.get_user(UserRole.USER)

        # Вводим неправильный email и неправильный пароль
        response = api_client.login("fake@nomail.ru", test_user.password)

        # Проверяем, что вход не удался
        assert response.success is False
        assert response.status_code in [400, 401, 403]

        # Проверяем отсутсвие токена
        assert 'token' not in response.data

    def test_already_logged_in_user(self, logged_in_user, api_client: MiniBankAPIClient):
        """Тест с уже залогиненным пользователем"""

        # Получаем данные пользователя USER
        test_user = settings.get_user(UserRole.USER)

        # Проверяем удачный вход
        assert logged_in_user['email'] == test_user.email
        assert logged_in_user['role'] == test_user.role.value

    def test_token_validation(self, logged_in_user, api_client: MiniBankAPIClient):
        """Тест валидации токена"""

        # Получаем данные пользователя USER
        test_user = settings.get_user(UserRole.USER)

        # Логинимся
        login_response = api_client.login(test_user.email, test_user.password)
        assert login_response.success is True

        # Проверяем валидность токена
        validation_response = api_client.validate_token()
        assert validation_response.success is True
        assert validation_response.status_code == 200

