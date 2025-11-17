from locust import HttpUser, task, between
import random

class HCRMUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login and get token"""
        response = self.client.post("/api/v1/auth/login/", json={
            "username": f"testuser{random.randint(1, 100)}",
            "password": "testpass123"
        })
        if response.status_code == 200:
            self.token = response.json().get('access')
            self.client.headers.update({'Authorization': f'Bearer {self.token}'})
    
    @task(3)
    def view_appointments(self):
        """Test viewing appointments"""
        self.client.get("/api/v1/appointments/")
    
    @task(2)
    def search_clinicians(self):
        """Test clinician search"""
        self.client.get("/api/v1/appointments/search/?q=doctor")
    
    @task(1)
    def view_profile(self):
        """Test profile retrieval"""
        self.client.get("/api/v1/patients/profile/")
    
    @task(1)
    def book_appointment(self):
        """Test appointment booking"""
        self.client.post("/api/v1/appointments/book/", json={
            "clinician": 1,
            "appointment_date": "2025-12-01",
            "appointment_time": "10:00:00",
            "reason_for_visit": "Load test"
        })

class ClinicianUser(HttpUser):
    wait_time = between(2, 5)
    
    def on_start(self):
        """Login as clinician"""
        response = self.client.post("/api/v1/auth/login/", json={
            "username": f"clinician{random.randint(1, 20)}",
            "password": "testpass123"
        })
        if response.status_code == 200:
            self.token = response.json().get('access')
            self.client.headers.update({'Authorization': f'Bearer {self.token}'})
    
    @task(3)
    def view_dashboard(self):
        """Test clinician dashboard"""
        self.client.get("/api/v1/appointments/dashboard/")
    
    @task(2)
    def view_patient_records(self):
        """Test EPR access"""
        patient_id = f"PAT{random.randint(1, 1000):06d}"
        self.client.get(f"/api/v1/records/{patient_id}/history/")
    
    @task(1)
    def add_clinical_note(self):
        """Test adding clinical notes"""
        self.client.post("/api/v1/records/notes/", json={
            "record_id": random.randint(1, 100),
            "note_content": "Load test clinical note"
        })