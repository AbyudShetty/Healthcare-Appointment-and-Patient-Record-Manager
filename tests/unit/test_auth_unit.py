import pytest
from authentication.models import User
from django.contrib.auth import authenticate


@pytest.mark.django_db
class TestAuthUnit:

    def test_create_user_with_role(self):
        """Unit: User created with correct role + fields"""
        user = User.objects.create_user(
            username="tester",
            password="pass123",
            role="CLINICIAN",
            email="tester@example.com"
        )

        assert user.username == "tester"
        assert user.role == "CLINICIAN"
        assert user.check_password("pass123")
        assert user.email == "tester@example.com"

    def test_authentication_success(self):
        """Unit: authenticate() returns user if credentials correct"""
        User.objects.create_user(username="authuser", password="mysecret")

        user = authenticate(username="authuser", password="mysecret")
        assert user is not None
        assert user.username == "authuser"

    def test_authentication_failure(self):
        """Unit: authenticate() returns None if wrong password"""
        User.objects.create_user(username="authuser2", password="passA")

        user = authenticate(username="authuser2", password="wrongpass")
        assert user is None