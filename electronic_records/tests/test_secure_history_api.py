# electronic_records/tests/test_secure_history_api.py
from django.urls import reverse
from django.test import TestCase
from django.conf import settings

from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from cryptography.fernet import Fernet

from django.contrib.auth import get_user_model
from patients.models import Patient
from electronic_records.models import PatientRecord, ClinicalNote
from electronic_records.utils import encrypt_field, decrypt_field

User = get_user_model()


class SecureHistoryApiTests(TestCase):
    def setUp(self):
        # --- Setup Fernet encryption key for test run ---
        key = Fernet.generate_key().decode()
        settings.MY_FERNET_KEY = key

        # --- Create users ---
        self.clinician = User.objects.create_user(
            username="clinician", password="testpass"
        )
        self.clinician.is_staff = True
        self.clinician.save()

        self.patient_user = User.objects.create_user(
            username="patient_user", password="testpass"
        )
        self.other_patient_user = User.objects.create_user(
            username="other_patient", password="testpass"
        )

        # --- Create patient (attach user if model requires it) ---
        patient_kwargs = {"patient_id": "TESTPAT001"}
        try:
            field_names = [f.name for f in Patient._meta.get_fields()]
            if "user" in field_names:
                patient_kwargs["user"] = self.patient_user
        except Exception:
            pass

        self.patient = Patient.objects.create(**patient_kwargs)

        # --- Create a patient record ---
        self.record = PatientRecord.objects.create(
            patient=self.patient,
            medical_history_encrypted="mh",
            diagnoses_encrypted="dx",
            medications_encrypted="meds",
            created_by=self.clinician,
        )

        # --- Create a ClinicalNote with plaintext here; model.save() will encrypt on create ---
        plaintext = "Patient has a mild allergy."
        self.note = ClinicalNote.objects.create(
            record=self.record,
            clinician=self.clinician,
            note_content_encrypted=plaintext,  # pass plaintext; model.save() encrypts
        )

        # --- API client & endpoint URL ---
        self.client = APIClient()
        self.url = reverse("secure-history", kwargs={"patient_id": self.patient.patient_id})

    def _auth_header_for(self, user):
        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)
        return {"HTTP_AUTHORIZATION": f"Bearer {access}"}

    def test_unauthenticated_returns_401(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 401)

    def test_patient_owner_can_view(self):
        headers = self._auth_header_for(self.patient_user)
        resp = self.client.get(self.url, **headers)
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        results = data.get("results") or data
        self.assertTrue(len(results) >= 1)

        notes = results[0].get("clinical_notes", [])
        self.assertTrue(len(notes) >= 1)

        decrypted_texts = []
        for n in notes:
            if n.get("decrypted_note"):
                decrypted_texts.append(n["decrypted_note"])
                continue
            token = n.get("note_content")
            if token:
                try:
                    decrypted_texts.append(decrypt_field(token))
                except Exception:
                    decrypted_texts.append(str(token))

        self.assertIn(
            "Patient has a mild allergy.",
            decrypted_texts,
            msg=f"Expected plaintext not found. Got decrypted_texts={decrypted_texts}",
        )

    def test_other_patient_forbidden(self):
        headers = self._auth_header_for(self.other_patient_user)
        resp = self.client.get(self.url, **headers)
        self.assertEqual(resp.status_code, 403)

    def test_clinician_can_view_any_patient(self):
        headers = self._auth_header_for(self.clinician)
        resp = self.client.get(self.url, **headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        results = data.get("results") or data
        self.assertTrue(len(results) >= 1)
