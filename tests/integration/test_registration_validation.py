import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from authentication.models import User
from patients.models import Patient


@pytest.mark.django_db
def test_registration_validates_and_creates_account():
    client = APIClient()
    url = reverse('patient-register')
    payload = {'user': {'username': 'new-patient', 'email': 'new@example.com',
                        'password': 'StrongPass123!', 'password_confirm': 'different'}}
    assert client.post(url, payload, format='json').status_code == 400
    assert not User.objects.filter(username='new-patient').exists()
    payload['user']['password_confirm'] = 'StrongPass123!'
    response = client.post(url, payload, format='json')
    assert response.status_code == 201
    user = User.objects.get(username='new-patient')
    assert user.check_password('StrongPass123!')
    assert Patient.objects.filter(user=user).exists()
    assert client.post(url, payload, format='json').status_code == 400
