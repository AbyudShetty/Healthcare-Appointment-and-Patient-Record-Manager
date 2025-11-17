"""
Seed database with test data for performance testing
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from patients.models import Patient
from appointments.models import Appointment, ClinicianSchedule
from electronic_records.models import PatientRecord, ClinicalNote
from datetime import date, time, timedelta
import random

User = get_user_model()

def seed_users(count=10000):
    """Create test users and patients"""
    print(f"Creating {count} users and patients...")
    
    users = []
    for i in range(count):
        users.append(User(
            username=f"testpatient_{i}",
            email=f"patient_{i}@hcrm.test",
            first_name=f"Patient{i}",
            last_name=f"User{i}",
            role="PATIENT"
        ))
    
    User.objects.bulk_create(users, batch_size=1000, ignore_conflicts=True)
    
    # Create patients
    patients = []
    for user in User.objects.filter(username__startswith="testpatient_"):
        if not hasattr(user, 'patient_profile'):
            patients.append(Patient(user=user))
    
    Patient.objects.bulk_create(patients, batch_size=1000, ignore_conflicts=True)
    print(f"✓ Created {len(patients)} patients")

def seed_clinicians(count=50):
    """Create test clinicians"""
    print(f"Creating {count} clinicians...")
    
    clinicians = []
    for i in range(count):
        clinicians.append(User(
            username=f"testclinician_{i}",
            email=f"clinician_{i}@hcrm.test",
            first_name=f"Dr. Clinician{i}",
            last_name=f"Smith{i}",
            role="CLINICIAN"
        ))
    
    User.objects.bulk_create(clinicians, batch_size=100, ignore_conflicts=True)
    print(f"✓ Created {count} clinicians")

def seed_appointments(count=5000):
    """Create test appointments"""
    print(f"Creating {count} appointments...")
    
    patients = list(Patient.objects.all()[:1000])
    clinicians = list(User.objects.filter(role="CLINICIAN")[:20])
    
    appointments = []
    for i in range(count):
        appointments.append(Appointment(
            patient=random.choice(patients),
            clinician=random.choice(clinicians),
            appointment_date=date.today() + timedelta(days=random.randint(-30, 30)),
            appointment_time=time(hour=random.randint(9, 17), minute=random.choice([0, 30])),
            reason_for_visit=f"Test visit {i}",
            status=random.choice(['SCHEDULED', 'COMPLETED', 'CANCELLED'])
        ))
    
    Appointment.objects.bulk_create(appointments, batch_size=1000, ignore_conflicts=True)
    print(f"✓ Created {count} appointments")

def seed_records(count=5000):
    """Create test patient records"""
    print(f"Creating {count} patient records...")
    
    patients = list(Patient.objects.all()[:count])
    clinicians = list(User.objects.filter(role="CLINICIAN")[:10])
    
    records = []
    for patient in patients:
        records.append(PatientRecord(
            patient=patient,
            medical_history_encrypted="Test medical history",
            diagnoses_encrypted="Test diagnosis",
            medications_encrypted="Test medications",
            created_by=random.choice(clinicians)
        ))
    
    PatientRecord.objects.bulk_create(records, batch_size=1000, ignore_conflicts=True)
    print(f"✓ Created {len(records)} patient records")

if __name__ == "__main__":
    print("🌱 Seeding HCRM database with test data...")
    print("=" * 50)
    
    seed_clinicians(50)
    seed_users(10000)
    seed_appointments(5000)
    seed_records(5000)
    
    print("=" * 50)
    print("✅ Database seeding complete!")