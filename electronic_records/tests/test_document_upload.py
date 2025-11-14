import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from authentication.models import User
from patients.models import Patient
from electronic_records.models import PatientDocument

@pytest.mark.django_db
class TestDocumentUpload:
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='patient1',
            password='testpass',
            role='PATIENT'
        )
        self.patient = Patient.objects.create(user=self.user)
        self.client.force_authenticate(user=self.user)
    
    def test_upload_pdf_document(self):
        """Test uploading a PDF document"""
        pdf_content = b'%PDF-1.4 fake pdf content'
        pdf_file = SimpleUploadedFile("report.pdf", pdf_content, content_type="application/pdf")
        
        response = self.client.post(
            '/api/v1/records/documents/upload/',
            {
                'document_type': 'LAB_REPORT',
                'file': pdf_file
            },
            format='multipart'
        )
        
        assert response.status_code == 201
        assert PatientDocument.objects.count() == 1
        doc = PatientDocument.objects.first()
        assert doc.original_filename == 'report.pdf'
    
    def test_reject_oversized_file(self):
        """Test rejection of files > 10MB"""
        large_file = SimpleUploadedFile(
            "large.pdf",
            b'x' * (11 * 1024 * 1024),  # 11MB
            content_type="application/pdf"
        )
        
        response = self.client.post(
            '/api/v1/records/documents/upload/',
            {
                'document_type': 'LAB_REPORT',
                'file': large_file
            },
            format='multipart'
        )
        
        assert response.status_code == 400