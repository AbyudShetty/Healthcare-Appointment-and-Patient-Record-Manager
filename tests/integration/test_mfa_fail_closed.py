import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from authentication.models import User


@pytest.mark.django_db
def test_mfa_enabled_user_cannot_bypass_second_factor():
    User.objects.create_user(username='mfa-user', password='Password123!', mfa_enabled=True)
    response = APIClient().post(reverse('token_obtain_pair'), {'username': 'mfa-user', 'password': 'Password123!'}, format='json')
    assert response.status_code == 401
    assert 'access' not in response.data
