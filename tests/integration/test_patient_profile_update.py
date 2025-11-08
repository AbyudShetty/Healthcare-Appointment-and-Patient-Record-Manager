import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from authentication.models import User
from patients.models import Patient


@pytest.mark.django_db
class TestPatientProfileUpdateView:
    """Integration test for patient profile update API (HCRM-F-002)"""

    def setup_method(self):
        self.client = APIClient()

    def test_authenticated_user_can_update_profile(self):
        """Patient should be able to update their profile"""
        # Setup: create user + patient
        user = User.objects.create_user(
            username="testuser",
            password="secure123",
            email="test@example.com",
            role="PATIENT",
        )
        patient = Patient.objects.create(user=user, address="Old Address")

        # Authenticate
        self.client.force_authenticate(user=user)

        # Send PATCH request
        url = reverse("patient-profile")
        response = self.client.patch(url, {"address": "New Address"}, format="json")

        # Assert
        assert response.status_code == 200
        patient.refresh_from_db()
        assert patient.address == "New Address"

    def test_unauthenticated_user_cannot_update_profile(self):
        """Unauthenticated user should not have access"""
        url = reverse("patient-profile")
        response = self.client.patch(url, {"address": "Hack Attempt"}, format="json")
        assert response.status_code == 401
