import pytest
from datetime import date, time
from appointments.models import Appointment
from authentication.models import User
from patients.models import Patient


@pytest.mark.django_db
class TestAppointmentModelUnit:

    def test_appointment_id_autogenerates(self):
        """Unit: Appointment ID should auto-generate as APT000001, APT000002…"""

        user = User.objects.create_user(username="doc", password="x", role="CLINICIAN")
        patient_user = User.objects.create_user(username="pat", password="x", role="PATIENT")
        patient = Patient.objects.create(user=patient_user)

        appt = Appointment.objects.create(
            patient=patient,
            clinician=user,
            appointment_date=date.today(),
            appointment_time=time(9, 0)
        )

        assert appt.appointment_id.startswith("APT")
        assert len(appt.appointment_id) == 9  # APT + 6 digits

    def test_appointment_string_representation(self):
        """Unit: __str__ returns readable appointment info"""
        c = User.objects.create_user(username="clin", password="x", role="CLINICIAN",
                                     first_name="John", last_name="Doc")
        p_user = User.objects.create_user(username="pat", password="x", role="PATIENT",
                                          first_name="Jane", last_name="Patient")
        p = Patient.objects.create(user=p_user)

        appt = Appointment.objects.create(
            patient=p,
            clinician=c,
            appointment_date=date.today(),
            appointment_time=time(10, 0)
        )

        text = str(appt)
        assert "APT" in text
        assert "John Doc" in text
        assert "Jane Patient" in text
